from collections import OrderedDict
from datetime import datetime

from flask import (
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user
from notifications_python_client.errors import HTTPError
from notifications_utils.clients.zendesk.zendesk_client import (
    NotifySupportTicket,
)

from app import (
    billing_api_client,
    current_service,
    email_branding_client,
    inbound_number_client,
    notification_api_client,
    organisations_client,
    service_api_client,
)
from app.event_handlers import (
    create_archive_service_event,
    create_resume_service_event,
    create_suspend_service_event,
)
from app.extensions import zendesk_client
from app.formatters import email_safe
from app.main import main
from app.main.forms import (
    AdminBillingDetailsForm,
    AdminNotesForm,
    AdminPreviewBrandingForm,
    AdminServiceAddDataRetentionForm,
    AdminServiceEditDataRetentionForm,
    AdminServiceInboundNumberForm,
    AdminServiceMessageLimitForm,
    AdminServiceRateLimitForm,
    AdminServiceSMSAllowanceForm,
    AdminSetEmailBrandingForm,
    AdminSetOrganisationForm,
    ChooseEmailBrandingForm,
    EstimateUsageForm,
    RenameServiceForm,
    SearchByNameForm,
    ServiceContactDetailsForm,
    ServiceEditInboundNumberForm,
    ServiceOnOffSettingForm,
    ServiceReplyToEmailForm,
    ServiceSmsSenderForm,
    ServiceSwitchChannelForm,
    SMSPrefixForm,
    SomethingElseBrandingForm,
)
from app.utils import DELIVERED_STATUSES, FAILURE_STATUSES, SENDING_STATUSES
from app.utils.branding import NHS_EMAIL_BRANDING_ID
from app.utils.branding import get_email_choices as get_email_branding_choices
from app.utils.time import parse_naive_dt
from app.utils.user import (
    user_has_permissions,
    user_is_gov_user,
    user_is_platform_admin,
)

PLATFORM_ADMIN_SERVICE_PERMISSIONS = OrderedDict([
    ('inbound_sms', {'title': 'Receive inbound SMS', 'requires': 'sms', 'endpoint': '.service_set_inbound_number'}),
    ('email_auth', {'title': 'Email authentication'}),
])


@main.route("/services/<uuid:service_id>/service-settings")
@user_has_permissions('manage_service', 'manage_api_keys')
def service_settings(service_id):
    return render_template(
        'views/service-settings.html',
        service_permissions=PLATFORM_ADMIN_SERVICE_PERMISSIONS,
        email_branding_options=ChooseEmailBrandingForm(current_service)
    )


@main.route("/services/<uuid:service_id>/service-settings/name", methods=['GET', 'POST'])
@user_has_permissions('manage_service')
def service_name_change(service_id):
    form = RenameServiceForm(name=current_service.name)

    if form.validate_on_submit():

        try:
            current_service.update(
                name=form.name.data,
                email_from=email_safe(form.name.data),
            )
        except HTTPError as http_error:
            if http_error.status_code == 400 and any(
                name_error_message.startswith('Duplicate service name')
                for name_error_message in http_error.message['name']
            ):
                form.name.errors.append('This service name is already in use')
            else:
                raise http_error
        else:
            return redirect(url_for('.service_settings', service_id=service_id))

    if current_service.organisation_type == 'local':
        return render_template(
            'views/service-settings/name-local.html',
            form=form,
        )

    return render_template(
        'views/service-settings/name.html',
        form=form,
    )


@main.route("/services/<uuid:service_id>/service-settings/request-to-go-live/estimate-usage", methods=['GET', 'POST'])
@user_has_permissions('manage_service')
def estimate_usage(service_id):

    form = EstimateUsageForm(
        volume_email=current_service.volume_email,
        volume_sms=current_service.volume_sms,
        consent_to_research={
            True: 'yes',
            False: 'no',
        }.get(current_service.consent_to_research),
    )

    if form.validate_on_submit():
        current_service.update(
            volume_email=form.volume_email.data,
            volume_sms=form.volume_sms.data,
            consent_to_research=(form.consent_to_research.data == 'yes'),
        )
        return redirect(url_for(
            'main.request_to_go_live',
            service_id=service_id,
        ))

    return render_template(
        'views/service-settings/estimate-usage.html',
        form=form,
    )


@main.route("/services/<uuid:service_id>/service-settings/request-to-go-live", methods=['GET'])
@user_has_permissions('manage_service')
def request_to_go_live(service_id):
    if current_service.live:
        return render_template('views/service-settings/service-already-live.html')

    return render_template(
        'views/service-settings/request-to-go-live.html'
    )


@main.route("/services/<uuid:service_id>/service-settings/request-to-go-live", methods=['POST'])
@user_has_permissions('manage_service')
@user_is_gov_user
def submit_request_to_go_live(service_id):
    ticket_message = render_template('support-tickets/go-live-request.txt') + '\n'

    ticket = NotifySupportTicket(
        subject=f'Request to go live - {current_service.name}',
        message=ticket_message,
        ticket_type=NotifySupportTicket.TYPE_QUESTION,
        user_name=current_user.name,
        user_email=current_user.email_address,
        requester_sees_message_content=False,
        org_id=current_service.organisation_id,
        org_type=current_service.organisation_type,
        service_id=current_service.id,
    )
    zendesk_client.send_ticket_to_zendesk(ticket)

    current_service.update(go_live_user=current_user.id)

    flash('Thanks for your request to go live. We’ll get back to you within one working day.', 'default')
    return redirect(url_for('.service_settings', service_id=service_id))


@main.route("/services/<uuid:service_id>/service-settings/switch-live", methods=["GET", "POST"])
@user_is_platform_admin
def service_switch_live(service_id):
    form = ServiceOnOffSettingForm(
        name="Make service live",
        enabled=not current_service.trial_mode
    )

    if form.validate_on_submit():
        current_service.update_status(live=form.enabled.data)
        return redirect(url_for('.service_settings', service_id=service_id))

    return render_template(
        'views/service-settings/set-service-setting.html',
        title="Make service live",
        form=form,
    )


@main.route("/services/<uuid:service_id>/service-settings/switch-count-as-live", methods=["GET", "POST"])
@user_is_platform_admin
def service_switch_count_as_live(service_id):

    form = ServiceOnOffSettingForm(
        name="Count in list of live services",
        enabled=current_service.count_as_live,
        truthy='Yes',
        falsey='No',
    )

    if form.validate_on_submit():
        current_service.update_count_as_live(form.enabled.data)
        return redirect(url_for('.service_settings', service_id=service_id))

    return render_template(
        'views/service-settings/set-service-setting.html',
        title="Count in list of live services",
        form=form,
    )


@main.route("/services/<uuid:service_id>/service-settings/permissions/<permission>", methods=["GET", "POST"])
@user_is_platform_admin
def service_set_permission(service_id, permission):
    if permission not in PLATFORM_ADMIN_SERVICE_PERMISSIONS:
        abort(404)

    title = PLATFORM_ADMIN_SERVICE_PERMISSIONS[permission]['title']
    form = ServiceOnOffSettingForm(
        name=title,
        enabled=current_service.has_permission(permission)
    )

    if form.validate_on_submit():
        current_service.force_permission(permission, on=form.enabled.data)

        return redirect(url_for(".service_settings", service_id=service_id))

    return render_template(
        'views/service-settings/set-service-setting.html',
        title=title,
        form=form,
    )


@main.route("/services/<uuid:service_id>/service-settings/archive", methods=['GET', 'POST'])
@user_has_permissions('manage_service')
def archive_service(service_id):
    if not current_service.active or not (
        current_service.trial_mode or current_user.platform_admin
    ):
        abort(403)
    if request.method == 'POST':
        # We need to purge the cache for the services users as otherwise, although they will have had their permissions
        # removed in the DB, they would still have permissions in the cache to view/edit/manage this service
        cached_service_user_ids = [user.id for user in current_service.active_users]

        service_api_client.archive_service(service_id, cached_service_user_ids)
        create_archive_service_event(service_id=service_id, archived_by_id=current_user.id)

        flash(
            '‘{}’ was deleted'.format(current_service.name),
            'default_with_tick',
        )
        return redirect(url_for('.choose_account'))
    else:
        flash(
            'Are you sure you want to delete ‘{}’? There’s no way to undo this.'.format(current_service.name),
            'delete',
        )
        return service_settings(service_id)


@main.route("/services/<uuid:service_id>/service-settings/suspend", methods=["GET", "POST"])
@user_is_platform_admin
def suspend_service(service_id):
    if request.method == 'POST':
        service_api_client.suspend_service(service_id)
        create_suspend_service_event(service_id=service_id, suspended_by_id=current_user.id)
        return redirect(url_for('.service_settings', service_id=service_id))
    else:
        flash("This will suspend the service and revoke all api keys. Are you sure you want to suspend this service?",
              'suspend')
        return service_settings(service_id)


@main.route("/services/<uuid:service_id>/service-settings/resume", methods=["GET", "POST"])
@user_is_platform_admin
def resume_service(service_id):
    if request.method == 'POST':
        service_api_client.resume_service(service_id)
        create_resume_service_event(service_id=service_id, resumed_by_id=current_user.id)
        return redirect(url_for('.service_settings', service_id=service_id))
    else:
        flash("This will resume the service. New api key are required for this service to use the API.", 'resume')
        return service_settings(service_id)


@main.route("/services/<uuid:service_id>/service-settings/send-files-by-email", methods=['GET', 'POST'])
@user_has_permissions('manage_service')
def send_files_by_email_contact_details(service_id):
    form = ServiceContactDetailsForm()
    contact_details = None

    if request.method == 'GET':
        contact_details = current_service.contact_link
        if contact_details:
            contact_type = check_contact_details_type(contact_details)
            field_to_update = getattr(form, contact_type)

            form.contact_details_type.data = contact_type
            field_to_update.data = contact_details

    if form.validate_on_submit():
        contact_type = form.contact_details_type.data

        current_service.update(
            contact_link=form.data[contact_type]
        )
        return redirect(url_for('.service_settings', service_id=current_service.id))

    return render_template(
        'views/service-settings/send-files-by-email.html', form=form, contact_details=contact_details
    )


@main.route("/services/<uuid:service_id>/service-settings/set-reply-to-email", methods=['GET'])
@user_has_permissions('manage_service')
def service_set_reply_to_email(service_id):
    return redirect(url_for('.service_email_reply_to', service_id=service_id))


@main.route("/services/<uuid:service_id>/service-settings/email-reply-to", methods=['GET'])
@user_has_permissions('manage_service', 'manage_api_keys')
def service_email_reply_to(service_id):
    return render_template('views/service-settings/email_reply_to.html')


@main.route("/services/<uuid:service_id>/service-settings/email-reply-to/add", methods=['GET', 'POST'])
@user_has_permissions('manage_service')
def service_add_email_reply_to(service_id):
    form = ServiceReplyToEmailForm()
    first_email_address = current_service.count_email_reply_to_addresses == 0
    is_default = first_email_address if first_email_address else form.is_default.data
    if form.validate_on_submit():
        if current_user.platform_admin:
            service_api_client.add_reply_to_email_address(
                service_id,
                email_address=form.email_address.data,
                is_default=is_default
            )
            return redirect(url_for('.service_email_reply_to', service_id=service_id))
        else:
            try:
                notification_id = service_api_client.verify_reply_to_email_address(
                    service_id, form.email_address.data
                )["data"]["id"]
            except HTTPError as e:
                if e.status_code == 409:
                    flash(e.message, 'error')
                    return redirect(url_for('.service_email_reply_to', service_id=service_id))
                else:
                    raise e
            return redirect(url_for(
                '.service_verify_reply_to_address',
                service_id=service_id,
                notification_id=notification_id,
                is_default=is_default
            ))

    return render_template(
        'views/service-settings/email-reply-to/add.html',
        form=form,
        first_email_address=first_email_address)


@main.route(
    "/services/<uuid:service_id>/service-settings/email-reply-to/<uuid:notification_id>/verify",
    methods=['GET', 'POST']
)
@user_has_permissions('manage_service')
def service_verify_reply_to_address(service_id, notification_id):
    replace = request.args.get('replace', False)
    is_default = request.args.get('is_default', False)
    return render_template(
        'views/service-settings/email-reply-to/verify.html',
        service_id=service_id,
        notification_id=notification_id,
        partials=get_service_verify_reply_to_address_partials(service_id, notification_id),
        verb=("Change" if replace else "Add"),
        replace=replace,
        is_default=is_default
    )


@main.route("/services/<uuid:service_id>/service-settings/email-reply-to/<uuid:notification_id>/verify.json")
@user_has_permissions('manage_service')
def service_verify_reply_to_address_updates(service_id, notification_id):
    return jsonify(**get_service_verify_reply_to_address_partials(service_id, notification_id))


def get_service_verify_reply_to_address_partials(service_id, notification_id):
    form = ServiceReplyToEmailForm()
    first_email_address = current_service.count_email_reply_to_addresses == 0
    notification = notification_api_client.get_notification(current_app.config["NOTIFY_SERVICE_ID"], notification_id)
    replace = request.args.get('replace', False)
    replace = False if replace == "False" else replace
    existing_is_default = False
    if replace:
        existing = current_service.get_email_reply_to_address(replace)
        existing_is_default = existing['is_default']
    verification_status = "pending"
    is_default = True if (request.args.get('is_default', False) == "True") else False
    if notification["status"] in DELIVERED_STATUSES:
        verification_status = "success"
        if notification["to"] not in [i["email_address"] for i in current_service.email_reply_to_addresses]:
            if replace:
                service_api_client.update_reply_to_email_address(
                    current_service.id, replace, email_address=notification["to"], is_default=is_default
                )
            else:
                service_api_client.add_reply_to_email_address(
                    current_service.id,
                    email_address=notification["to"],
                    is_default=is_default
                )
    seconds_since_sending = (
        datetime.utcnow() - parse_naive_dt(notification['created_at'])
    ).seconds
    if notification["status"] in FAILURE_STATUSES or (
        notification["status"] in SENDING_STATUSES and
        seconds_since_sending > current_app.config['REPLY_TO_EMAIL_ADDRESS_VALIDATION_TIMEOUT']
    ):
        verification_status = "failure"
        form.email_address.data = notification['to']
        form.is_default.data = is_default
    return {
        'status': render_template(
            'views/service-settings/email-reply-to/_verify-updates.html',
            reply_to_email_address=notification["to"],
            service_id=current_service.id,
            notification_id=notification_id,
            verification_status=verification_status,
            is_default=is_default,
            existing_is_default=existing_is_default,
            form=form,
            first_email_address=first_email_address,
            replace=replace
        ),
        'stop': 0 if verification_status == "pending" else 1
    }


@main.route(
    "/services/<uuid:service_id>/service-settings/email-reply-to/<uuid:reply_to_email_id>/edit",
    methods=['GET', 'POST'],
    endpoint="service_edit_email_reply_to"
)
@main.route(
    "/services/<uuid:service_id>/service-settings/email-reply-to/<uuid:reply_to_email_id>/delete",
    methods=['GET'],
    endpoint="service_confirm_delete_email_reply_to"
)
@user_has_permissions('manage_service')
def service_edit_email_reply_to(service_id, reply_to_email_id):
    form = ServiceReplyToEmailForm()
    reply_to_email_address = current_service.get_email_reply_to_address(reply_to_email_id)

    if request.method == 'GET':
        form.email_address.data = reply_to_email_address['email_address']
        form.is_default.data = reply_to_email_address['is_default']

    show_choice_of_default_checkbox = not reply_to_email_address['is_default']

    if form.validate_on_submit():
        if form.email_address.data == reply_to_email_address["email_address"] or current_user.platform_admin:
            service_api_client.update_reply_to_email_address(
                current_service.id,
                reply_to_email_id=reply_to_email_id,
                email_address=form.email_address.data,
                is_default=True if reply_to_email_address['is_default'] else form.is_default.data
            )
            return redirect(url_for('.service_email_reply_to', service_id=service_id))
        try:
            notification_id = service_api_client.verify_reply_to_email_address(
                service_id, form.email_address.data
            )["data"]["id"]
        except HTTPError as e:
            if e.status_code == 409:
                flash(e.message, 'error')
                return redirect(url_for('.service_email_reply_to', service_id=service_id))
            else:
                raise e
        return redirect(url_for(
            '.service_verify_reply_to_address',
            service_id=service_id,
            notification_id=notification_id,
            is_default=True if reply_to_email_address['is_default'] else form.is_default.data,
            replace=reply_to_email_id
        ))

    if (request.endpoint == "main.service_confirm_delete_email_reply_to"):
        flash("Are you sure you want to delete this reply-to email address?", 'delete')
    return render_template(
        'views/service-settings/email-reply-to/edit.html',
        form=form,
        reply_to_email_address_id=reply_to_email_id,
        show_choice_of_default_checkbox=show_choice_of_default_checkbox
    )


@main.route(
    "/services/<uuid:service_id>/service-settings/email-reply-to/<uuid:reply_to_email_id>/delete",
    methods=['POST']
)
@user_has_permissions('manage_service')
def service_delete_email_reply_to(service_id, reply_to_email_id):
    service_api_client.delete_reply_to_email_address(
        service_id=current_service.id,
        reply_to_email_id=reply_to_email_id,
    )
    return redirect(url_for('.service_email_reply_to', service_id=service_id))


@main.route("/services/<uuid:service_id>/service-settings/set-inbound-number", methods=['GET', 'POST'])
@user_has_permissions('manage_service')
def service_set_inbound_number(service_id):
    available_inbound_numbers = inbound_number_client.get_available_inbound_sms_numbers()
    inbound_numbers_value_and_label = [
        (number['id'], number['number']) for number in available_inbound_numbers['data']
    ]
    no_available_numbers = available_inbound_numbers['data'] == []
    form = AdminServiceInboundNumberForm(
        inbound_number_choices=inbound_numbers_value_and_label
    )

    if form.validate_on_submit():
        service_api_client.add_sms_sender(
            current_service.id,
            sms_sender=form.inbound_number.data,
            is_default=True,
            inbound_number_id=form.inbound_number.data
        )
        current_service.force_permission('inbound_sms', on=True)
        return redirect(url_for('.service_settings', service_id=service_id))

    return render_template(
        'views/service-settings/set-inbound-number.html',
        form=form,
        no_available_numbers=no_available_numbers,
    )


@main.route("/services/<uuid:service_id>/service-settings/sms-prefix", methods=['GET', 'POST'])
@user_has_permissions('manage_service')
def service_set_sms_prefix(service_id):

    form = SMSPrefixForm(enabled=current_service.prefix_sms)

    form.enabled.label.text = 'Start all text messages with ‘{}:’'.format(current_service.name)

    if form.validate_on_submit():
        current_service.update(
            prefix_sms=form.enabled.data
        )
        return redirect(url_for('.service_settings', service_id=service_id))

    return render_template(
        'views/service-settings/sms-prefix.html',
        form=form
    )


@main.route("/services/<uuid:service_id>/service-settings/set-international-sms", methods=['GET', 'POST'])
@user_has_permissions('manage_service')
def service_set_international_sms(service_id):
    form = ServiceOnOffSettingForm(
        'Send text messages to international phone numbers',
        enabled=current_service.has_permission('international_sms'),
    )
    if form.validate_on_submit():
        current_service.force_permission(
            'international_sms',
            on=form.enabled.data,
        )
        return redirect(
            url_for(".service_settings", service_id=service_id)
        )
    return render_template(
        'views/service-settings/set-international-sms.html',
        form=form,
    )


@main.route("/services/<uuid:service_id>/service-settings/set-inbound-sms", methods=['GET'])
@user_has_permissions('manage_service')
def service_set_inbound_sms(service_id):
    return render_template(
        'views/service-settings/set-inbound-sms.html',
    )


@main.route("/services/<uuid:service_id>/service-settings/set-<channel>", methods=['GET', 'POST'])
@user_has_permissions('manage_service')
def service_set_channel(service_id, channel):

    if channel not in {'email', 'sms'}:
        abort(404)

    form = ServiceSwitchChannelForm(
        channel=channel,
        enabled=current_service.has_permission(channel)
    )

    if form.validate_on_submit():
        current_service.force_permission(
            channel,
            on=form.enabled.data,
        )
        return redirect(
            url_for(".service_settings", service_id=service_id)
        )

    return render_template(
        'views/service-settings/set-{}.html'.format(channel),
        form=form,
    )


@main.route("/services/<uuid:service_id>/service-settings/set-auth-type", methods=['GET'])
@user_has_permissions('manage_service')
def service_set_auth_type(service_id):
    return render_template(
        'views/service-settings/set-auth-type.html',
    )


@main.route("/services/<uuid:service_id>/service-settings/sms-sender", methods=['GET'])
@user_has_permissions('manage_service', 'manage_api_keys')
def service_sms_senders(service_id):
    return render_template(
        'views/service-settings/sms-senders.html',
    )


@main.route("/services/<uuid:service_id>/service-settings/sms-sender/add", methods=['GET', 'POST'])
@user_has_permissions('manage_service')
def service_add_sms_sender(service_id):
    form = ServiceSmsSenderForm()
    first_sms_sender = current_service.count_sms_senders == 0
    if form.validate_on_submit():
        service_api_client.add_sms_sender(
            current_service.id,
            sms_sender=form.sms_sender.data.replace('\r', '') or None,
            is_default=first_sms_sender if first_sms_sender else form.is_default.data
        )
        return redirect(url_for('.service_sms_senders', service_id=service_id))
    return render_template(
        'views/service-settings/sms-sender/add.html',
        form=form,
        first_sms_sender=first_sms_sender)


@main.route(
    "/services/<uuid:service_id>/service-settings/sms-sender/<uuid:sms_sender_id>/edit",
    methods=['GET', 'POST'],
    endpoint="service_edit_sms_sender"
)
@main.route(
    "/services/<uuid:service_id>/service-settings/sms-sender/<uuid:sms_sender_id>/delete",
    methods=['GET'],
    endpoint="service_confirm_delete_sms_sender"
)
@user_has_permissions('manage_service')
def service_edit_sms_sender(service_id, sms_sender_id):
    sms_sender = current_service.get_sms_sender(sms_sender_id)
    is_inbound_number = sms_sender['inbound_number_id']
    if is_inbound_number:
        form = ServiceEditInboundNumberForm(is_default=sms_sender['is_default'])
    else:
        form = ServiceSmsSenderForm(**sms_sender)

    if form.validate_on_submit():
        service_api_client.update_sms_sender(
            current_service.id,
            sms_sender_id=sms_sender_id,
            sms_sender=sms_sender['sms_sender'] if is_inbound_number else form.sms_sender.data.replace('\r', ''),
            is_default=True if sms_sender['is_default'] else form.is_default.data
        )
        return redirect(url_for('.service_sms_senders', service_id=service_id))

    form.is_default.data = sms_sender['is_default']
    if (request.endpoint == "main.service_confirm_delete_sms_sender"):
        flash("Are you sure you want to delete this text message sender?", 'delete')
    return render_template(
        'views/service-settings/sms-sender/edit.html',
        form=form,
        sms_sender=sms_sender,
        inbound_number=is_inbound_number,
        sms_sender_id=sms_sender_id
    )


@main.route(
    "/services/<uuid:service_id>/service-settings/sms-sender/<uuid:sms_sender_id>/delete",
    methods=['POST'],
)
@user_has_permissions('manage_service')
def service_delete_sms_sender(service_id, sms_sender_id):
    service_api_client.delete_sms_sender(
        service_id=current_service.id,
        sms_sender_id=sms_sender_id,
    )
    return redirect(url_for('.service_sms_senders', service_id=service_id))


@main.route("/services/<uuid:service_id>/service-settings/set-free-sms-allowance", methods=['GET', 'POST'])
@user_is_platform_admin
def set_free_sms_allowance(service_id):

    form = AdminServiceSMSAllowanceForm(free_sms_allowance=current_service.free_sms_fragment_limit)

    if form.validate_on_submit():
        billing_api_client.create_or_update_free_sms_fragment_limit(service_id, form.free_sms_allowance.data)

        return redirect(url_for('.service_settings', service_id=service_id))

    return render_template(
        'views/service-settings/set-free-sms-allowance.html',
        form=form,
    )


@main.route("/services/<uuid:service_id>/service-settings/set-message-limit", methods=['GET', 'POST'])
@user_is_platform_admin
def set_message_limit(service_id):

    form = AdminServiceMessageLimitForm(message_limit=current_service.message_limit)

    if form.validate_on_submit():
        current_service.update(message_limit=form.message_limit.data)

        return redirect(url_for('.service_settings', service_id=service_id))

    return render_template(
        'views/service-settings/set-message-limit.html',
        form=form,
    )


@main.route("/services/<uuid:service_id>/service-settings/set-rate-limit", methods=['GET', 'POST'])
@user_is_platform_admin
def set_rate_limit(service_id):

    form = AdminServiceRateLimitForm(rate_limit=current_service.rate_limit)

    if form.validate_on_submit():
        current_service.update(rate_limit=form.rate_limit.data)

        return redirect(url_for('.service_settings', service_id=service_id))

    return render_template(
        'views/service-settings/set-rate-limit.html',
        form=form,
    )


@main.route("/services/<uuid:service_id>/service-settings/set-email-branding", methods=['GET', 'POST'])
@user_is_platform_admin
def service_set_email_branding(service_id):
    email_branding = email_branding_client.get_all_email_branding()

    form = AdminSetEmailBrandingForm(
        all_branding_options=get_branding_as_value_and_label(email_branding),
        current_branding=current_service.email_branding_id,
    )

    if form.validate_on_submit():
        return redirect(url_for(
            '.service_preview_email_branding',
            service_id=service_id,
            branding_style=form.branding_style.data,
        ))

    return render_template(
        'views/service-settings/set-email-branding.html',
        form=form,
        search_form=SearchByNameForm()
    )


@main.route("/services/<uuid:service_id>/service-settings/preview-email-branding", methods=['GET', 'POST'])
@user_is_platform_admin
def service_preview_email_branding(service_id):
    branding_style = request.args.get('branding_style', None)

    form = AdminPreviewBrandingForm(branding_style=branding_style)

    if form.validate_on_submit():
        current_service.update(
            email_branding=form.branding_style.data
        )
        return redirect(url_for('.service_settings', service_id=service_id))

    return render_template(
        'views/service-settings/preview-email-branding.html',
        form=form,
        service_id=service_id,
        action=url_for('main.service_preview_email_branding', service_id=service_id),
    )


@main.route("/services/<uuid:service_id>/service-settings/link-service-to-organisation", methods=['GET', 'POST'])
@user_is_platform_admin
def link_service_to_organisation(service_id):

    all_organisations = organisations_client.get_organisations()

    form = AdminSetOrganisationForm(
        choices=convert_dictionary_to_wtforms_choices_format(all_organisations, 'id', 'name'),
        organisations=current_service.organisation_id
    )

    if form.validate_on_submit():
        if form.organisations.data != current_service.organisation_id:
            organisations_client.update_service_organisation(
                service_id,
                form.organisations.data
            )
        return redirect(url_for('.service_settings', service_id=service_id))

    return render_template(
        'views/service-settings/link-service-to-organisation.html',
        has_organisations=all_organisations,
        form=form,
        search_form=SearchByNameForm(),
    )


def create_email_branding_zendesk_ticket(form_option_selected, detail=None):
    form = ChooseEmailBrandingForm(current_service)

    ticket_message = render_template(
        'support-tickets/branding-request.txt',
        current_branding=current_service.email_branding_name,
        branding_requested=dict(form.options.choices)[form_option_selected],
        detail=detail,
    )
    ticket = NotifySupportTicket(
        subject=f'Email branding request - {current_service.name}',
        message=ticket_message,
        ticket_type=NotifySupportTicket.TYPE_QUESTION,
        user_name=current_user.name,
        user_email=current_user.email_address,
        org_id=current_service.organisation_id,
        org_type=current_service.organisation_type,
        service_id=current_service.id
    )
    zendesk_client.send_ticket_to_zendesk(ticket)


@main.route("/services/<uuid:service_id>/service-settings/email-branding", methods=['GET', 'POST'])
@user_has_permissions('manage_service')
def email_branding_request(service_id):
    form = ChooseEmailBrandingForm(current_service)
    branding_name = current_service.email_branding_name
    if form.validate_on_submit():
        return redirect(
            url_for(
                f'.email_branding_{form.options.data}',
                service_id=current_service.id,
            )
        )

    return render_template(
        'views/service-settings/branding/email-branding-options.html',
        form=form,
        branding_name=branding_name,
    )


def check_email_branding_allowed_for_service(branding):
    allowed_branding_for_service = dict(
        get_email_branding_choices(current_service)
    )

    if branding not in allowed_branding_for_service:
        abort(404)


@main.route("/services/<uuid:service_id>/service-settings/email-branding/govuk", methods=['GET', 'POST'])
@user_has_permissions('manage_service')
def email_branding_govuk(service_id):
    check_email_branding_allowed_for_service('govuk')

    if request.method == 'POST':
        current_service.update(email_branding=None)

        flash('You’ve updated your email branding', 'default')
        return redirect(url_for('.service_settings', service_id=current_service.id))

    return render_template('views/service-settings/branding/email-branding-govuk.html')


@main.route("/services/<uuid:service_id>/service-settings/email-branding/govuk-and-org", methods=['GET', 'POST'])
@user_has_permissions('manage_service')
def email_branding_govuk_and_org(service_id):
    check_email_branding_allowed_for_service('govuk_and_org')

    if request.method == 'POST':
        create_email_branding_zendesk_ticket('govuk_and_org')

        flash('Thanks for your branding request. We’ll get back to you within one working day.', 'default')
        return redirect(url_for('.service_settings', service_id=current_service.id))

    return render_template('views/service-settings/branding/email-branding-govuk-org.html')


@main.route("/services/<uuid:service_id>/service-settings/email-branding/nhs", methods=['GET', 'POST'])
@user_has_permissions('manage_service')
def email_branding_nhs(service_id):
    check_email_branding_allowed_for_service('nhs')

    if request.method == 'POST':
        current_service.update(email_branding=NHS_EMAIL_BRANDING_ID)

        flash('You’ve updated your email branding', 'default')
        return redirect(url_for('.service_settings', service_id=current_service.id))

    return render_template(
        'views/service-settings/branding/email-branding-nhs.html',
        nhs_branding_id=NHS_EMAIL_BRANDING_ID
    )


@main.route("/services/<uuid:service_id>/service-settings/email-branding/organisation", methods=['GET', 'POST'])
@user_has_permissions('manage_service')
def email_branding_organisation(service_id):
    check_email_branding_allowed_for_service('organisation')

    if request.method == 'POST':
        create_email_branding_zendesk_ticket('organisation')

        flash('Thanks for your branding request. We’ll get back to you within one working day.', 'default')
        return redirect(url_for('.service_settings', service_id=current_service.id))

    return render_template('views/service-settings/branding/email-branding-organisation.html')


@main.route("/services/<uuid:service_id>/service-settings/email-branding/something-else", methods=['GET', 'POST'])
@user_has_permissions('manage_service')
def email_branding_something_else(service_id):
    form = SomethingElseBrandingForm()

    if form.validate_on_submit():
        create_email_branding_zendesk_ticket('something_else', detail=form.something_else.data)

        flash('Thanks for your branding request. We’ll get back to you within one working day.', 'default')
        return redirect(url_for('.service_settings', service_id=current_service.id))

    return render_template(
        'views/service-settings/branding/email-branding-something-else.html',
        form=form,
        branding_options=ChooseEmailBrandingForm(current_service)
    )


@main.route("/services/<uuid:service_id>/data-retention", methods=['GET'])
@user_is_platform_admin
def data_retention(service_id):
    return render_template(
        'views/service-settings/data-retention.html',
    )


@main.route("/services/<uuid:service_id>/data-retention/add", methods=['GET', 'POST'])
@user_is_platform_admin
def add_data_retention(service_id):
    form = AdminServiceAddDataRetentionForm()
    if form.validate_on_submit():
        service_api_client.create_service_data_retention(service_id,
                                                         form.notification_type.data,
                                                         form.days_of_retention.data)
        return redirect(url_for('.data_retention', service_id=service_id))
    return render_template(
        'views/service-settings/data-retention/add.html',
        form=form
    )


@main.route("/services/<uuid:service_id>/data-retention/<uuid:data_retention_id>/edit", methods=['GET', 'POST'])
@user_is_platform_admin
def edit_data_retention(service_id, data_retention_id):
    data_retention_item = current_service.get_data_retention_item(data_retention_id)
    form = AdminServiceEditDataRetentionForm(days_of_retention=data_retention_item['days_of_retention'])
    if form.validate_on_submit():
        service_api_client.update_service_data_retention(service_id, data_retention_id, form.days_of_retention.data)
        return redirect(url_for('.data_retention', service_id=service_id))
    return render_template(
        'views/service-settings/data-retention/edit.html',
        form=form,
        data_retention_id=data_retention_id,
        notification_type=data_retention_item['notification_type']
    )


@main.route("/services/<uuid:service_id>/notes", methods=['GET', 'POST'])
@user_is_platform_admin
def edit_service_notes(service_id):
    form = AdminNotesForm(notes=current_service.notes)

    if form.validate_on_submit():

        if form.notes.data == current_service.notes:
            return redirect(url_for('.service_settings', service_id=service_id))

        current_service.update(
            notes=form.notes.data
        )
        return redirect(url_for('.service_settings', service_id=service_id))

    return render_template(
        'views/service-settings/edit-service-notes.html',
        form=form,
    )


@main.route("/services/<uuid:service_id>/edit-billing-details", methods=['GET', 'POST'])
@user_is_platform_admin
def edit_service_billing_details(service_id):
    form = AdminBillingDetailsForm(
        billing_contact_email_addresses=current_service.billing_contact_email_addresses,
        billing_contact_names=current_service.billing_contact_names,
        billing_reference=current_service.billing_reference,
        purchase_order_number=current_service.purchase_order_number,
        notes=current_service.notes,
    )

    if form.validate_on_submit():
        current_service.update(
            billing_contact_email_addresses=form.billing_contact_email_addresses.data,
            billing_contact_names=form.billing_contact_names.data,
            billing_reference=form.billing_reference.data,
            purchase_order_number=form.purchase_order_number.data,
            notes=form.notes.data,
        )
        return redirect(url_for('.service_settings', service_id=service_id))

    return render_template(
        'views/service-settings/edit-service-billing-details.html',
        form=form,
    )


def get_branding_as_value_and_label(email_branding):
    return [
        (branding['id'], branding['name'])
        for branding in email_branding
    ]


def convert_dictionary_to_wtforms_choices_format(dictionary, value, label):
    return [
        (item[value], item[label]) for item in dictionary
    ]


def check_contact_details_type(contact_details):
    if contact_details.startswith('http'):
        return 'url'
    elif '@' in contact_details:
        return 'email_address'
    else:
        return 'phone_number'
