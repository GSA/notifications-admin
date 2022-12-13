import itertools
from datetime import datetime
from io import BytesIO
from zipfile import BadZipFile

from flask import flash, redirect, render_template, request, send_file, url_for
from notifications_utils.insensitive_dict import InsensitiveDict
from notifications_utils.recipients import RecipientCSV
from notifications_utils.sanitise_text import SanitiseASCII
from xlrd.biffh import XLRDError
from xlrd.xldate import XLDateError

from app import current_service
from app.main import main
from app.main.forms import CsvUploadForm
from app.models.contact_list import ContactList
from app.utils import unicode_truncate
from app.utils.csv import Spreadsheet, get_errors_for_csv
from app.utils.pagination import generate_next_dict, generate_previous_dict
from app.utils.templates import get_sample_template
from app.utils.user import user_has_permissions

MAX_FILE_UPLOAD_SIZE = 2 * 1024 * 1024  # 2MB


@main.route("/services/<uuid:service_id>/uploads")
@user_has_permissions()
def uploads(service_id):
    # No tests have been written, this has been quickly prepared for user research.
    # It's also very like that a new view will be created to show uploads.
    uploads = current_service.get_page_of_uploads(page=request.args.get('page'))

    prev_page = None
    if uploads.prev_page:
        prev_page = generate_previous_dict('main.uploads', service_id, uploads.current_page)
    next_page = None
    if uploads.next_page:
        next_page = generate_next_dict('main.uploads', service_id, uploads.current_page)

    if uploads.current_page == 1:
        listed_uploads = (
            current_service.contact_lists +
            current_service.scheduled_jobs +
            uploads
        )
    else:
        listed_uploads = uploads

    return render_template(
        'views/jobs/jobs.html',
        jobs=listed_uploads,
        prev_page=prev_page,
        next_page=next_page,
        now=datetime.utcnow().isoformat(),
    )


@main.route("/services/<uuid:service_id>/upload-contact-list", methods=['GET', 'POST'])
@user_has_permissions('send_messages')
def upload_contact_list(service_id):
    form = CsvUploadForm()

    if form.validate_on_submit():
        try:
            upload_id = ContactList.upload(
                current_service.id,
                Spreadsheet.from_file_form(form).as_dict,
            )
            file_name_metadata = unicode_truncate(
                SanitiseASCII.encode(form.file.data.filename),
                1600
            )
            ContactList.set_metadata(
                current_service.id,
                upload_id,
                original_file_name=file_name_metadata
            )
            return redirect(url_for(
                '.check_contact_list',
                service_id=service_id,
                upload_id=upload_id,
            ))
        except (UnicodeDecodeError, BadZipFile, XLRDError):
            flash('Could not read {}. Try using a different file format.'.format(
                form.file.data.filename
            ))
        except (XLDateError):
            flash((
                '{} contains numbers or dates that Notify cannot understand. '
                'Try formatting all columns as ‘text’ or export your file as CSV.'
            ).format(
                form.file.data.filename
            ))
    elif form.errors:
        # just show the first error, as we don't expect the form to have more
        # than one, since it only has one field
        first_field_errors = list(form.errors.values())[0]
        flash(first_field_errors[0])

    return render_template(
        'views/uploads/contact-list/upload.html',
        form=form,
        allowed_file_extensions=Spreadsheet.ALLOWED_FILE_EXTENSIONS,
    )


@main.route(
    "/services/<uuid:service_id>/check-contact-list/<uuid:upload_id>",
    methods=['GET', 'POST'],
)
@user_has_permissions('send_messages')
def check_contact_list(service_id, upload_id):

    form = CsvUploadForm()

    contents = ContactList.download(service_id, upload_id)
    first_row = contents.splitlines()[0].strip().rstrip(',') if contents else ''
    original_file_name = ContactList.get_metadata(service_id, upload_id).get('original_file_name', '')

    template_type = InsensitiveDict({
        'email address': 'email',
        'phone number': 'sms',
    }).get(first_row)

    recipients = RecipientCSV(
        contents,
        template=get_sample_template(template_type or 'sms'),
        guestlist=itertools.chain.from_iterable(
            [user.name, user.mobile_number, user.email_address]
            for user in current_service.active_users
        ) if current_service.trial_mode else None,
        allow_international_sms=current_service.has_permission('international_sms'),
        max_initial_rows_shown=50,
        max_errors_shown=50,
    )

    non_empty_column_headers = list(filter(None, recipients.column_headers))

    if len(non_empty_column_headers) > 1 or not template_type or not recipients:
        return render_template(
            'views/uploads/contact-list/too-many-columns.html',
            recipients=recipients,
            original_file_name=original_file_name,
            template_type=template_type,
            form=form,
            allowed_file_extensions=Spreadsheet.ALLOWED_FILE_EXTENSIONS
        )

    if recipients.too_many_rows or not len(recipients):
        return render_template(
            'views/uploads/contact-list/column-errors.html',
            recipients=recipients,
            original_file_name=original_file_name,
            form=form,
            allowed_file_extensions=Spreadsheet.ALLOWED_FILE_EXTENSIONS
        )

    row_errors = get_errors_for_csv(recipients, template_type)
    if row_errors:
        return render_template(
            'views/uploads/contact-list/row-errors.html',
            recipients=recipients,
            original_file_name=original_file_name,
            row_errors=row_errors,
            form=form,
            allowed_file_extensions=Spreadsheet.ALLOWED_FILE_EXTENSIONS
        )

    if recipients.has_errors:
        return render_template(
            'views/uploads/contact-list/column-errors.html',
            recipients=recipients,
            original_file_name=original_file_name,
            form=form,
            allowed_file_extensions=Spreadsheet.ALLOWED_FILE_EXTENSIONS
        )

    metadata_kwargs = {
        'row_count': len(recipients),
        'valid': True,
        'original_file_name': original_file_name,
        'template_type': template_type
    }

    ContactList.set_metadata(service_id, upload_id, **metadata_kwargs)

    return render_template(
        'views/uploads/contact-list/ok.html',
        recipients=recipients,
        original_file_name=original_file_name,
        upload_id=upload_id,
    )


@main.route("/services/<uuid:service_id>/save-contact-list/<uuid:upload_id>", methods=['POST'])
@user_has_permissions('send_messages')
def save_contact_list(service_id, upload_id):
    ContactList.create(current_service.id, upload_id)
    return redirect(url_for(
        '.uploads',
        service_id=current_service.id,
    ))


@main.route("/services/<uuid:service_id>/contact-list/<uuid:contact_list_id>", methods=['GET'])
@user_has_permissions('send_messages')
def contact_list(service_id, contact_list_id):
    contact_list = ContactList.from_id(contact_list_id, service_id=service_id)
    return render_template(
        'views/uploads/contact-list/contact-list.html',
        contact_list=contact_list,
        jobs=contact_list.get_jobs(
            page=1,
            limit_days=current_service.get_days_of_retention(contact_list.template_type),
        ),
    )


@main.route("/services/<uuid:service_id>/contact-list/<uuid:contact_list_id>/delete", methods=['GET', 'POST'])
@user_has_permissions('manage_templates')
def delete_contact_list(service_id, contact_list_id):
    contact_list = ContactList.from_id(contact_list_id, service_id=service_id)

    if request.method == 'POST':
        contact_list.delete()
        return redirect(url_for(
            '.uploads',
            service_id=service_id,
        ))

    flash([
        f"Are you sure you want to delete ‘{contact_list.original_file_name}’?",
    ], 'delete')

    return render_template(
        'views/uploads/contact-list/contact-list.html',
        contact_list=contact_list,
        confirm_delete_banner=True,
    )


@main.route("/services/<uuid:service_id>/contact-list/<uuid:contact_list_id>.csv", methods=['GET'])
@user_has_permissions('send_messages')
def download_contact_list(service_id, contact_list_id):
    contact_list = ContactList.from_id(contact_list_id, service_id=service_id)
    return send_file(
        path_or_file=BytesIO(contact_list.contents.encode('utf-8')),
        attachment_filename=contact_list.saved_file_name,
        as_attachment=True,
    )
