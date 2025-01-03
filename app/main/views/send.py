import os
import time
import uuid
from string import ascii_uppercase
from zipfile import BadZipFile

from flask import (
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user
from markupsafe import Markup
from notifications_python_client.errors import HTTPError
from xlrd.biffh import XLRDError
from xlrd.xldate import XLDateError

from app import (
    current_service,
    job_api_client,
    nl2br,
    notification_api_client,
    service_api_client,
)
from app.main import main
from app.main.forms import (
    ChooseTimeForm,
    CsvUploadForm,
    SetSenderForm,
    get_placeholder_form_instance,
)
from app.main.views.user_profile import set_timezone
from app.models.user import Users
from app.s3_client.s3_csv_client import (
    get_csv_metadata,
    s3download,
    s3upload,
    set_metadata_on_csv_upload,
)
from app.utils import (
    PermanentRedirect,
    hilite,
    should_skip_template_page,
    unicode_truncate,
)
from app.utils.csv import Spreadsheet, get_errors_for_csv
from app.utils.templates import get_template
from app.utils.user import user_has_permissions
from notifications_utils import SMS_CHAR_COUNT_LIMIT
from notifications_utils.insensitive_dict import InsensitiveDict
from notifications_utils.recipients import RecipientCSV, first_column_headings
from notifications_utils.sanitise_text import SanitiseASCII


def get_example_csv_fields(column_headers, use_example_as_example, submitted_fields):
    if use_example_as_example:
        return ["example" for header in column_headers]
    elif submitted_fields:
        return [submitted_fields.get(header) for header in column_headers]
    else:
        return list(column_headers)


def get_example_csv_rows(template, use_example_as_example=True, submitted_fields=False):
    return {
        "email": (
            ["test@example.com"]
            if use_example_as_example
            else [current_user.email_address]
        ),
        "sms": (
            ["12223334444"] if use_example_as_example else [current_user.mobile_number]
        ),
    }[template.template_type] + get_example_csv_fields(
        (
            placeholder
            for placeholder in template.placeholders
            if placeholder
            not in InsensitiveDict.from_keys(
                first_column_headings[template.template_type]
            )
        ),
        use_example_as_example,
        submitted_fields,
    )


@main.route(
    "/services/<uuid:service_id>/send/<uuid:template_id>/csv", methods=["GET", "POST"]
)
@user_has_permissions("send_messages", restrict_admin_usage=True)
def send_messages(service_id, template_id):
    notification_count = service_api_client.get_notification_count(service_id)
    remaining_messages = current_service.message_limit - notification_count

    db_template = current_service.get_template_with_user_permission_or_403(
        template_id, current_user
    )

    email_reply_to = None
    sms_sender = None

    if db_template["template_type"] == "email":
        email_reply_to = get_email_reply_to_address_from_session()
    elif db_template["template_type"] == "sms":
        sms_sender = get_sms_sender_from_session()

    if db_template["template_type"] not in current_service.available_template_types:
        return redirect(
            url_for(
                ".action_blocked",
                service_id=service_id,
                notification_type=db_template["template_type"],
                return_to="view_template",
                template_id=template_id,
            )
        )

    template = get_template(
        db_template,
        current_service,
        show_recipient=True,
        email_reply_to=email_reply_to,
        sms_sender=sms_sender,
    )

    form = CsvUploadForm()
    if form.validate_on_submit():
        try:
            upload_id = s3upload(
                service_id,
                Spreadsheet.from_file_form(form).as_dict,
            )
            file_name_metadata = unicode_truncate(
                SanitiseASCII.encode(form.file.data.filename), 1600
            )
            set_metadata_on_csv_upload(
                service_id, upload_id, original_file_name=file_name_metadata
            )
            return redirect(
                url_for(
                    ".check_messages",
                    service_id=service_id,
                    upload_id=upload_id,
                    template_id=template.id,
                )
            )
        except (UnicodeDecodeError, BadZipFile, XLRDError):
            flash(
                "Could not read {}. Try using a different file format.".format(
                    form.file.data.filename
                )
            )
        except XLDateError:
            flash(
                (
                    "{} contains numbers or dates that Notify cannot understand. "
                    "Try formatting all columns as ‘text’ or export your file as CSV."
                ).format(form.file.data.filename)
            )
    elif form.errors:
        # just show the first error, as we don't expect the form to have more
        # than one, since it only has one field
        first_field_errors = list(form.errors.values())[0]
        error_message = '<span class="usa-error-message">'
        error_message = f"{error_message}{first_field_errors[0]}"
        error_message = f"{error_message}</span>"
        error_message = Markup(error_message)
        flash(error_message)
    column_headings = get_spreadsheet_column_headings_from_template(template)

    return render_template(
        "views/send.html",
        template=template,
        column_headings=list(ascii_uppercase[: len(column_headings)]),
        example=[column_headings, get_example_csv_rows(template)],
        form=form,
        allowed_file_extensions=Spreadsheet.ALLOWED_FILE_EXTENSIONS,
        remaining_messages=remaining_messages,
    )


@main.route("/services/<uuid:service_id>/send/<uuid:template_id>.csv", methods=["GET"])
@user_has_permissions("send_messages", "manage_templates")
def get_example_csv(service_id, template_id):
    template = get_template(
        service_api_client.get_service_template(service_id, template_id)["data"],
        current_service,
    )
    return (
        Spreadsheet.from_rows(
            [
                get_spreadsheet_column_headings_from_template(template),
                get_example_csv_rows(template),
            ]
        ).as_csv_data,
        200,
        {
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": 'inline; filename="{}.csv"'.format(template.name),
        },
    )


@main.route(
    "/services/<uuid:service_id>/send/<uuid:template_id>/set-sender",
    methods=["GET", "POST"],
)
@user_has_permissions("send_messages", restrict_admin_usage=True)
def set_sender(service_id, template_id):
    session["sender_id"] = None
    redirect_to_one_off = redirect(
        url_for(".send_one_off", service_id=service_id, template_id=template_id)
    )

    template = current_service.get_template_with_user_permission_or_403(
        template_id, current_user
    )

    sender_details = get_sender_details(service_id, template["template_type"])

    sender_details = remove_notify_from_sender_options(sender_details)

    if len(sender_details) == 1:
        session["sender_id"] = sender_details[0]["id"]

    if len(sender_details) <= 1:
        return redirect_to_one_off

    sender_context = get_sender_context(sender_details, template["template_type"])

    form = SetSenderForm(
        sender=sender_context["default_id"],
        sender_choices=sender_context["value_and_label"],
        sender_label=sender_context["description"],
    )
    option_hints = {sender_context["default_id"]: "(Default)"}
    if sender_context.get("receives_text_message", None):
        option_hints.update(
            {sender_context["receives_text_message"]: "(Receives replies)"}
        )
    if sender_context.get("default_and_receives", None):
        option_hints = {
            sender_context["default_and_receives"]: "(Default and receives replies)"
        }

    # extend all radios that need hint text
    form.sender.param_extensions = {"items": []}
    for item_id, _item_value in form.sender.choices:
        if item_id in option_hints:
            extensions = {"hint": {"text": option_hints[item_id]}}
        else:
            extensions = (
                {}
            )  # if no extensions needed, send an empty dict to preserve order of items
        form.sender.param_extensions["items"].append(extensions)

    if form.validate_on_submit():
        session["sender_id"] = form.sender.data
        return redirect(
            url_for(".send_one_off", service_id=service_id, template_id=template_id)
        )

    return render_template(
        "views/templates/set-sender.html",
        form=form,
        template_id=template_id,
        sender_context={
            "title": sender_context["title"],
            "description": sender_context["description"],
        },
        option_hints=option_hints,
    )


def remove_notify_from_sender_options(sender_details):
    # Remove US Notify/Notify.gov from users list of sender
    # options during message send flow
    sender_details = [
        sender for sender in sender_details if verify_sender_options(sender)
    ]

    return sender_details


def verify_sender_options(sender):
    if sender.get("sms_sender") in ["Notify.gov", "US Notify"] and sender["is_default"]:
        return True
    if sender.get("sms_sender") not in ["Notify.gov", "US Notify"]:
        return True

    return False


def get_sender_context(sender_details, template_type):
    context = {
        "email": {
            "title": "Where should replies come back to?",
            "description": "Where should replies come back to?",
            "field_name": "email_address",
        },
        "sms": {
            "title": "Who should the message come from?",
            "description": "Who should the message come from?",
            "field_name": "sms_sender",
        },
    }[template_type]

    sender_format = context["field_name"]

    context["default_id"] = next(
        sender["id"] for sender in sender_details if sender["is_default"]
    )
    if template_type == "sms":
        inbound = [
            sender["id"] for sender in sender_details if sender["inbound_number_id"]
        ]
        if inbound:
            context["receives_text_message"] = next(iter(inbound))
        if context["default_id"] == context.get("receives_text_message", None):
            context["default_and_receives"] = context["default_id"]

    context["value_and_label"] = [
        (sender["id"], nl2br(sender[sender_format])) for sender in sender_details
    ]
    return context


def get_sender_details(service_id, template_type):
    api_call = {
        "email": service_api_client.get_reply_to_email_addresses,
        "sms": service_api_client.get_sms_senders,
    }[template_type]
    return api_call(service_id)


@main.route("/services/<uuid:service_id>/send/<uuid:template_id>/one-off")
@user_has_permissions("send_messages", restrict_admin_usage=True)
def send_one_off(service_id, template_id):
    session["recipient"] = None
    session["placeholders"] = {}

    db_template = current_service.get_template_with_user_permission_or_403(
        template_id, current_user
    )

    if db_template["template_type"] not in current_service.available_template_types:
        return redirect(
            url_for(
                ".action_blocked",
                service_id=service_id,
                notification_type=db_template["template_type"],
                return_to="view_template",
                template_id=template_id,
            )
        )

    return redirect(
        url_for(
            ".send_one_off_step",
            service_id=service_id,
            template_id=template_id,
            step_index=0,
        )
    )


def get_notification_check_endpoint(service_id, template):
    return redirect(
        url_for(
            "main.check_notification",
            service_id=service_id,
            template_id=template.id,
        )
    )


@main.route(
    "/services/<uuid:service_id>/send/<uuid:template_id>/one-off/step-<int:step_index>",
    methods=["GET", "POST"],
)
@user_has_permissions("send_messages", restrict_admin_usage=True)
def send_one_off_step(service_id, template_id, step_index):
    if {"recipient", "placeholders"} - set(session.keys()):
        return redirect(
            url_for(
                ".send_one_off",
                service_id=service_id,
                template_id=template_id,
            )
        )

    db_template = current_service.get_template_with_user_permission_or_403(
        template_id, current_user
    )

    email_reply_to = None
    sms_sender = None
    if db_template["template_type"] == "email":
        email_reply_to = get_email_reply_to_address_from_session()
    elif db_template["template_type"] == "sms":
        sms_sender = (
            get_sms_sender_from_session()
        )  # TODO: verify default sender is Notify.gov

    template_values = get_recipient_and_placeholders_from_session(
        db_template["template_type"]
    )

    template = get_template(
        db_template,
        current_service,
        show_recipient=True,
        email_reply_to=email_reply_to,
        sms_sender=sms_sender,
    )

    placeholders = fields_to_fill_in(template)

    try:
        current_placeholder = placeholders[step_index]
    except IndexError:
        if all_placeholders_in_session(placeholders):
            return get_notification_check_endpoint(service_id, template)
        return redirect(
            url_for(
                ".send_one_off",
                service_id=service_id,
                template_id=template_id,
            )
        )

    form = get_placeholder_form_instance(
        current_placeholder,
        dict_to_populate_from=get_normalised_placeholders_from_session(),
        template_type=template.template_type,
        allow_international_phone_numbers=current_service.has_permission(
            "international_sms"
        ),
    )

    if form.validate_on_submit():
        # if it's the first input (phone/email), we store against `recipient` as well, for easier extraction.
        # Only if we're not on the test route, since that will already have the user's own number set
        if step_index == 0:
            session["recipient"] = form.placeholder_value.data

        session["placeholders"][current_placeholder] = form.placeholder_value.data

        if all_placeholders_in_session(placeholders):
            return get_notification_check_endpoint(service_id, template)

        return redirect(
            url_for(
                request.endpoint,
                service_id=service_id,
                template_id=template_id,
                step_index=step_index + 1,
            )
        )

    back_link = get_back_link(service_id, template, step_index, placeholders)

    template.values = template_values
    template.values[current_placeholder] = None

    return render_template(
        "views/send-test.html",
        page_title=get_send_test_page_title(
            template.template_type,
            entering_recipient=not session["recipient"],
            name=template.name,
        ),
        template=template,
        form=form,
        skip_link=get_skip_link(step_index, template),
        back_link=back_link,
        link_to_upload=(
            request.endpoint == "main.send_one_off_step" and step_index == 0
        ),
        errors=form.errors if form.errors else None,
    )


def _check_messages(service_id, template_id, upload_id, preview_row, **kwargs):
    try:
        # The happy path is that the job doesn’t already exist, so the
        # API will return a 404 and the client will raise HTTPError.
        job_api_client.get_job(service_id, upload_id)

        # the job exists already - so go back to the templates page
        # If we just return a `redirect` (302) object here, we'll get
        # errors when we try and unpack in the check_messages route.
        # Rasing a werkzeug.routing redirect means that doesn't happen.
        raise PermanentRedirect(
            url_for(
                "main.send_messages", service_id=service_id, template_id=template_id
            )
        )
    except HTTPError as e:
        if e.status_code != 404:
            raise

    notification_count = service_api_client.get_notification_count(service_id)
    remaining_messages = current_service.message_limit - notification_count

    contents = s3download(service_id, upload_id)
    db_template = current_service.get_template_with_user_permission_or_403(
        template_id, current_user
    )

    email_reply_to = None
    sms_sender = None
    if db_template["template_type"] == "email":
        email_reply_to = get_email_reply_to_address_from_session()
    elif db_template["template_type"] == "sms":
        sms_sender = get_sms_sender_from_session()

    template = get_template(
        db_template,
        current_service,
        show_recipient=False,
        email_reply_to=email_reply_to,
        sms_sender=sms_sender,
        **kwargs,
    )

    allow_list = []
    if current_service.trial_mode:
        # Adding the simulated numbers to allow list
        # so they can be sent in trial mode
        for user in Users(service_id):
            allow_list.extend([user.name, user.mobile_number, user.email_address])
        # Failed sms number
        allow_list.extend(
            ["simulated user (fail)", "+14254147167", "simulated@simulated.gov"]
        )
        # Success sms number
        allow_list.extend(
            ["simulated user (success)", "+14254147755", "simulatedtwo@simulated.gov"]
        )
    else:
        allow_list = None
    recipients = RecipientCSV(
        contents,
        template=template,
        max_initial_rows_shown=50,
        max_errors_shown=50,
        guestlist=allow_list,
        remaining_messages=remaining_messages,
        allow_international_sms=current_service.has_permission("international_sms"),
    )

    if request.args.get("from_test"):
        # TODO: may not be required after letters code removed
        back_link = url_for(
            "main.send_one_off", service_id=service_id, template_id=template.id
        )
        back_link_from_preview = url_for(
            "main.send_one_off", service_id=service_id, template_id=template.id
        )
        choose_time_form = None
    else:
        back_link = url_for(
            "main.send_messages", service_id=service_id, template_id=template.id
        )
        back_link_from_preview = url_for(
            "main.check_messages",
            service_id=service_id,
            template_id=template.id,
            upload_id=upload_id,
        )
        choose_time_form = ChooseTimeForm()

    if preview_row < 2:
        abort(404)

    if preview_row < len(recipients) + 2:
        template.values = recipients[preview_row - 2].recipient_and_personalisation
    elif preview_row > 2:
        abort(404)

    original_file_name = get_csv_metadata(service_id, upload_id).get(
        "original_file_name", ""
    )

    return dict(
        recipients=recipients,
        template=template,
        errors=recipients.has_errors,
        row_errors=get_errors_for_csv(recipients, template.template_type),
        count_of_recipients=len(recipients),
        count_of_displayed_recipients=len(list(recipients.displayed_rows)),
        original_file_name=original_file_name,
        upload_id=upload_id,
        form=CsvUploadForm(),
        remaining_messages=remaining_messages,
        choose_time_form=choose_time_form,
        back_link=back_link,
        back_link_from_preview=back_link_from_preview,
        first_recipient_column=recipients.recipient_column_headers[0],
        preview_row=preview_row,
        sent_previously=job_api_client.has_sent_previously(
            service_id, template.id, db_template["version"], original_file_name
        ),
        template_id=template_id,
    )


@main.route(
    "/services/<uuid:service_id>/<uuid:template_id>/check/<uuid:upload_id>",
    methods=["GET"],
)
@main.route(
    "/services/<uuid:service_id>/<uuid:template_id>/check/<uuid:upload_id>/row-<int:row_index>",
    methods=["GET"],
)
@user_has_permissions("send_messages", restrict_admin_usage=True)
def check_messages(service_id, template_id, upload_id, row_index=2):
    data = _check_messages(service_id, template_id, upload_id, row_index)
    data["allowed_file_extensions"] = Spreadsheet.ALLOWED_FILE_EXTENSIONS

    if (
        data["recipients"].too_many_rows
        or not data["count_of_recipients"]
        or not data["recipients"].has_recipient_columns
        or data["recipients"].duplicate_recipient_column_headers
        or data["recipients"].missing_column_headers
        or data["sent_previously"]
    ):
        return render_template("views/check/column-errors.html", **data)

    if data["row_errors"]:
        return render_template("views/check/row-errors.html", **data)

    if data["errors"]:
        return render_template("views/check/column-errors.html", **data)

    metadata_kwargs = {
        "notification_count": data["count_of_recipients"],
        "template_id": template_id,
        "valid": True,
        "original_file_name": data.get("original_file_name", ""),
    }

    if session.get("sender_id"):
        metadata_kwargs["sender_id"] = session["sender_id"]

    set_metadata_on_csv_upload(service_id, upload_id, **metadata_kwargs)

    return render_template("views/check/ok.html", **data)


@main.route(
    "/services/<uuid:service_id>/<uuid:template_id>/check/<uuid:upload_id>/preview",
    methods=["POST"],
)
@main.route(
    "/services/<uuid:service_id>/<uuid:template_id>/check/<uuid:upload_id>/preview/row-<int:row_index>",
    methods=["POST"],
)
@user_has_permissions("send_messages", restrict_admin_usage=True)
def preview_job(service_id, template_id, upload_id, row_index=2):
    session["scheduled_for"] = request.form.get("scheduled_for", "")
    data = _check_messages(
        service_id, template_id, upload_id, row_index, force_hide_sender=True
    )

    return render_template(
        "views/check/preview.html",
        scheduled_for=session["scheduled_for"],
        **data,
    )


@main.route("/services/<uuid:service_id>/start-job/<uuid:upload_id>", methods=["POST"])
@user_has_permissions("send_messages", restrict_admin_usage=True)
def start_job(service_id, upload_id):
    scheduled_for = session.pop("scheduled_for", None)
    job_api_client.create_job(
        upload_id,
        service_id,
        scheduled_for=scheduled_for,
    )

    session.pop("sender_id", None)

    return redirect(
        url_for(
            "main.view_job",
            job_id=upload_id,
            service_id=service_id,
        )
    )


def fields_to_fill_in(template, prefill_current_user=False):
    if not prefill_current_user:
        return first_column_headings[template.template_type] + list(
            template.placeholders
        )

    if template.template_type == "sms":
        session["recipient"] = current_user.mobile_number
        session["placeholders"]["phone number"] = current_user.mobile_number
    else:
        session["recipient"] = current_user.email_address
        session["placeholders"]["email address"] = current_user.email_address

    return list(template.placeholders)


def get_normalised_placeholders_from_session():
    return InsensitiveDict(session.get("placeholders", {}))


def get_recipient_and_placeholders_from_session(template_type):
    placeholders = get_normalised_placeholders_from_session()

    if template_type == "sms":
        placeholders["phone_number"] = session["recipient"]
    else:
        placeholders["email_address"] = session["recipient"]

    return placeholders


def all_placeholders_in_session(placeholders):
    return all(
        get_normalised_placeholders_from_session().get(placeholder, False)
        not in (False, None)
        for placeholder in placeholders
    )


def get_send_test_page_title(template_type, entering_recipient, name=None):
    if entering_recipient:
        return "Select recipients"
    return "Personalize this message"


def get_back_link(
    service_id,
    template,
    step_index,
    placeholders=None,
    preview=False,
):
    if preview:
        return url_for(
            "main.check_notification",
            service_id=service_id,
            template_id=template.id,
        )

    if step_index == 0:
        if should_skip_template_page(template._template):
            return url_for(
                ".choose_template",
                service_id=service_id,
            )
        else:
            return url_for(
                ".view_template",
                service_id=service_id,
                template_id=template.id,
            )

    return url_for(
        "main.send_one_off_step",
        service_id=service_id,
        template_id=template.id,
        step_index=step_index - 1,
    )


def get_skip_link(step_index, template):
    if (
        request.endpoint == "main.send_one_off_step"
        and step_index == 0
        and template.template_type in ("sms", "email")
        and not (template.template_type == "sms" and current_user.mobile_number is None)
        and current_user.has_permissions("manage_templates", "manage_service")
    ):
        return (
            "Use my {}".format(first_column_headings[template.template_type][0]),
            url_for(
                ".send_one_off_to_myself",
                service_id=current_service.id,
                template_id=template.id,
            ),
        )


@main.route(
    "/services/<uuid:service_id>/template/<uuid:template_id>/one-off/send-to-myself",
    methods=["GET"],
)
@user_has_permissions("send_messages", restrict_admin_usage=True)
def send_one_off_to_myself(service_id, template_id):
    current_app.logger.info("Send one off to myself")
    try:
        db_template = current_service.get_template_with_user_permission_or_403(
            template_id, current_user
        )
    except Exception:
        current_app.logger.exception("Couldnt get template for one off")
        # Use 406 just because we're limited to certain codes here and it will point us back to a problem here
        abort(406)

    if db_template["template_type"] not in ("sms", "email"):
        abort(404)

    # We aren't concerned with creating the exact template (for example adding recipient and sender names)
    # we just want to create enough to use `fields_to_fill_in`
    template = get_template(
        db_template,
        current_service,
    )
    fields_to_fill_in(template, prefill_current_user=True)

    return redirect(
        url_for(
            "main.send_one_off_step",
            service_id=service_id,
            template_id=template_id,
            step_index=1,
        )
    )


@main.route(
    "/services/<uuid:service_id>/template/<uuid:template_id>/notification/check",
    methods=["GET"],
)
@user_has_permissions("send_messages", restrict_admin_usage=True)
def check_notification(service_id, template_id):
    return render_template(
        "views/notifications/check.html",
        **_check_notification(service_id, template_id, show_recipient=True),
    )


def _check_notification(service_id, template_id, exception=None, **kwargs):
    db_template = current_service.get_template_with_user_permission_or_403(
        template_id, current_user
    )
    email_reply_to = None
    sms_sender = None
    if db_template["template_type"] == "email":
        email_reply_to = get_email_reply_to_address_from_session()
    elif db_template["template_type"] == "sms":
        sms_sender = get_sms_sender_from_session()
    template = get_template(
        db_template,
        current_service,
        email_reply_to=email_reply_to,
        sms_sender=sms_sender,
        **kwargs,
    )
    placeholders = fields_to_fill_in(template)

    back_link = get_back_link(service_id, template, len(placeholders), placeholders)

    back_link_from_preview = get_back_link(
        service_id, template, len(placeholders), placeholders, preview=True
    )

    choose_time_form = ChooseTimeForm()

    if (not session.get("recipient")) or not all_placeholders_in_session(
        template.placeholders
    ):
        raise PermanentRedirect(back_link)

    template.values = get_recipient_and_placeholders_from_session(
        template.template_type
    )
    return dict(
        template=template,
        back_link=back_link,
        back_link_from_preview=back_link_from_preview,
        choose_time_form=choose_time_form,
        **(get_template_error_dict(exception) if exception else {}),
    )


def get_template_error_dict(exception):
    # TODO: Make API return some computer-friendly identifier as well as the end user error messages
    if "service is in trial mode" in exception.message:
        error = "not-allowed-to-send-to"
    elif "Exceeded send limits" in exception.message:
        error = "too-many-messages"
    # the error from the api is changing for message-too-long, but we need both until the api is deployed.
    elif (
        "Content for template has a character count greater than the limit of"
        in exception.message
    ):
        error = "message-too-long"
    elif "Text messages cannot be longer than" in exception.message:
        error = "message-too-long"
    else:
        raise exception

    return {
        "error": error,
        "SMS_CHAR_COUNT_LIMIT": SMS_CHAR_COUNT_LIMIT,
        "current_service": current_service,
        # used to trigger CSV specific err msg content, so not needed for single notification errors.
        "original_file_name": False,
    }


@main.route(
    "/services/<uuid:service_id>/template/<uuid:template_id>/notification/check/preview",
    methods=["POST"],
)
@user_has_permissions("send_messages", restrict_admin_usage=True)
def preview_notification(service_id, template_id):
    recipient = get_recipient()
    if not recipient:
        return redirect(
            url_for(
                ".send_one_off",
                service_id=service_id,
                template_id=template_id,
            )
        )

    session["scheduled_for"] = request.form.get("scheduled_for", "")

    return render_template(
        "views/notifications/preview.html",
        **_check_notification(
            service_id, template_id, show_recipient=False, force_hide_sender=True
        ),
        scheduled_for=session["scheduled_for"],
        recipient=recipient,
    )


@main.route(
    "/services/<uuid:service_id>/template/<uuid:template_id>/notification/check",
    methods=["POST"],
)
@user_has_permissions("send_messages", restrict_admin_usage=True)
def send_notification(service_id, template_id):
    recipient = get_recipient()

    if not recipient:
        return redirect(
            url_for(
                ".send_one_off",
                service_id=service_id,
                template_id=template_id,
            )
        )
    upload_id = _send_notification(service_id, template_id)

    session.pop("recipient", "")
    session.pop("placeholders", "")

    # We have to wait for the job to run and create the notification in the database
    time.sleep(0.1)
    notifications = notification_api_client.get_notifications_for_service(
        service_id, job_id=upload_id, include_one_off=True
    )
    attempts = 0

    # The response can come back in different forms of incompleteness
    while (
        notifications["total"] == 0
        and notifications["notifications"] == []
        and attempts < 50
    ):
        notifications = notification_api_client.get_notifications_for_service(
            service_id, job_id=upload_id, include_one_off=True
        )
        time.sleep(0.1)
        attempts = attempts + 1

    if notifications["total"] == 0 and attempts == 50:
        # This shows the job we auto-generated for the user
        return redirect(
            url_for(
                "main.view_job",
                service_id=service_id,
                job_id=upload_id,
            )
        )
    total = notifications["total"]
    current_app.logger.info(
        hilite(
            f"job_id: {upload_id} has notifications: {total} and attempts: {attempts}"
        )
    )
    return redirect(
        url_for(
            ".view_job",
            service_id=service_id,
            job_id=upload_id,
            # used to show the final step of the tour (help=3) or not show
            # a back link on a just sent one off notification (help=0)
            help=request.args.get("help"),
        )
    )


def _send_notification(service_id, template_id):
    scheduled_for = session.pop("scheduled_for", "")

    keys = []
    values = []
    # Guarantee that the real phone number comes last, because some
    # users will have placeholders like "add your second phone number"
    # or something like as custom placeholders.
    for k, v in session["placeholders"].items():
        if k != "phone number":
            keys.append(k)
            values.append(v)
    if "phone number" in session["placeholders"].keys():
        keys.append("phone number")
        values.append(session["placeholders"]["phone number"])

    data = ",".join(keys)
    vals = ",".join(values)
    data = f"{data}\r\n{vals}"
    filename = (
        f"one-off-{uuid.uuid4()}.csv"  # {current_user.name} removed from filename
    )
    my_data = {"filename": filename, "template_id": template_id, "data": data}
    upload_id = s3upload(service_id, my_data)
    # To debug messages that the user reports have not been sent, we log
    # the csv filename and the job id.  The user will give us the file name,
    # so we can search on that to obtain the job id, which we can use elsewhere
    # on the API side to find out what happens to the message.
    current_app.logger.info(
        hilite(
            f"One-off file: {filename} job_id: {upload_id} s3 location: {service_id}-service-notify/{upload_id}.csv"
        )
    )

    # For load testing we want to skip these checks.  They are doing some fine-grained
    # comparison about what is in the preview, but the load test just blast messages
    # and doesn't care about the preview.
    if os.getenv("NOTIFY_ENVIRONMENT") not in ("development", "staging", "demo"):
        form = CsvUploadForm()
        form.file.data = my_data
        form.file.name = filename
        check_message_output = check_messages(service_id, template_id, upload_id, 2)
        if "You cannot send to" in check_message_output:
            return check_messages(service_id, template_id, upload_id, 2)

    job_api_client.create_job(
        upload_id,
        service_id,
        scheduled_for=scheduled_for,
        template_id=template_id,
        original_file_name=filename,
        notification_count=1,
        valid="True",
    )
    return upload_id


def get_email_reply_to_address_from_session():
    if session.get("sender_id"):
        return current_service.get_email_reply_to_address(session["sender_id"])[
            "email_address"
        ]


def get_sms_sender_from_session():
    sender_id = session.get("sender_id")
    if sender_id:
        sms_sender = current_service.get_sms_sender(session["sender_id"])["sms_sender"]
        current_app.logger.info(f"SMS Sender ({sender_id}) #: {sms_sender}")
        return sms_sender
    else:
        current_app.logger.error("No SMS Sender!!!!!!")


def get_spreadsheet_column_headings_from_template(template):
    column_headings = []

    recipient_columns = first_column_headings[template.template_type]

    for column_heading in recipient_columns + list(template.placeholders):
        if column_heading not in InsensitiveDict.from_keys(column_headings):
            column_headings.append(column_heading)

    return column_headings


def get_recipient():
    set_timezone()
    if {"recipient", "placeholders"} - set(session.keys()):
        return None

    return session["recipient"] or InsensitiveDict(session["placeholders"]).get(
        "address line 1"
    )
