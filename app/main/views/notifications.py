# -*- coding: utf-8 -*-
from datetime import datetime

from flask import (
    Response,
    flash,
    jsonify,
    render_template,
    request,
    stream_with_context,
    url_for,
)
from flask_login import current_user

from app import current_service, job_api_client, notification_api_client
from app.main import main
from app.notify_client.api_key_api_client import KEY_TYPE_TEST
from app.s3_client.s3_csv_client import delete_report, report_upload
from app.utils import (
    DELIVERED_STATUSES,
    FAILURE_STATUSES,
    get_help_argument,
    parse_filter_args,
    set_status_filters,
)
from app.utils.csv import generate_notifications_csv, get_user_preferred_timezone
from app.utils.templates import get_template
from app.utils.user import user_has_permissions


@main.route("/services/<uuid:service_id>/notification/<uuid:notification_id>")
@user_has_permissions("view_activity", "send_messages")
def view_notification(service_id, notification_id, error_message=None):
    if error_message:
        flash(error_message)

    notification = notification_api_client.get_notification(
        service_id, str(notification_id)
    )
    notification["template"].update({"reply_to_text": notification["reply_to_text"]})

    personalisation = get_all_personalisation_from_notification(notification)

    template = get_template(
        notification["template"],
        current_service,
        show_recipient=True,
        redact_missing_personalisation=True,
        sms_sender=notification["reply_to_text"],
        email_reply_to=notification["reply_to_text"],
    )
    template.values = personalisation
    if notification["job"]:
        job = job_api_client.get_job(service_id, notification["job"]["id"])["data"]
    else:
        job = None

    if get_help_argument() or request.args.get("help") == "0":
        # help=0 is set when you’ve just sent a notification. We
        # only want to show the back link when you’ve navigated to a
        # notification, not when you’ve just sent it.
        back_link = None
    elif request.args.get("from_job"):
        back_link = url_for(
            "main.view_job",
            service_id=current_service.id,
            job_id=request.args.get("from_job"),
        )
    else:
        back_link = url_for(
            "main.view_notifications",
            service_id=current_service.id,
            message_type=template.template_type,
            status="sending,delivered,failed",
        )

    return render_template(
        "views/notifications/notification.html",
        finished=(notification["status"] in (DELIVERED_STATUSES + FAILURE_STATUSES)),
        notification_status=notification["status"],
        message=error_message,
        uploaded_file_name="Report",
        template=template,
        job=job,
        updates_url=url_for(
            ".view_notification_updates",
            service_id=service_id,
            notification_id=notification["id"],
            status=request.args.get("status"),
            help=get_help_argument(),
        ),
        partials=get_single_notification_partials(notification),
        created_by=notification.get("created_by"),
        created_at=notification["created_at"],
        updated_at=notification["sent_at"],
        help=get_help_argument(),
        notification_id=notification["id"],
        can_receive_inbound=(current_service.has_permission("inbound_sms")),
        sent_with_test_key=(notification.get("key_type") == KEY_TYPE_TEST),
        back_link=back_link,
    )


@main.route("/services/<uuid:service_id>/notification/<uuid:notification_id>.json")
@user_has_permissions("view_activity", "send_messages")
def view_notification_updates(service_id, notification_id):
    return jsonify(
        **get_single_notification_partials(
            notification_api_client.get_notification(service_id, notification_id)
        )
    )


def get_single_notification_partials(notification):
    return {
        "status": render_template(
            "partials/notifications/status.html",
            notification=notification,
            sent_with_test_key=(notification.get("key_type") == KEY_TYPE_TEST),
        ),
    }


def get_all_personalisation_from_notification(notification):
    if notification["template"].get("redact_personalisation"):
        notification["personalisation"] = {}

    if notification["template"]["template_type"] == "email":
        notification["personalisation"]["email_address"] = notification["to"]

    if notification["template"]["template_type"] == "sms":
        notification["personalisation"]["phone_number"] = notification["to"]

    return notification["personalisation"]


@main.route("/services/<uuid:service_id>/download-notifications.csv")
@user_has_permissions("view_activity")
def download_notifications_csv(service_id):
    filter_args = parse_filter_args(request.args)
    filter_args["status"] = set_status_filters(filter_args)
    number_of_days = request.args["number_of_days"]
    service_data_retention_days = current_service.get_days_of_retention(
        filter_args.get("message_type")[0], number_of_days
    )
    file_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    file_time = f"{file_time} {get_user_preferred_timezone()}"

    csv = generate_notifications_csv(
        service_id=service_id,
        job_id=None,
        status=filter_args.get("status"),
        page=request.args.get("page", 1),
        page_size=10000,
        format_for_csv=True,
        template_type=filter_args.get("message_type"),
        limit_days=service_data_retention_days,
    )

    # START asynchronous reporting block
    csv_file = "".join(csv)
    file_location = f"reports/{service_id}/{current_user.id}/{service_data_retention_days}/report.csv"

    # TODO these are some capabilities we will probably need when
    # report generation becomes asynchronous.

    # old_content = report_download(file_location)
    # current_app.logger.info(f"OLD CONTENT IS {old_content}")
    # reports = get_downloadable_reports(current_user.id, service_id)

    # TODO these are to support asynchronous report generation.
    # Leaving them commented in so they get exercised.
    delete_report(file_location)
    report_upload(file_location, csv_file)
    # END asynchronous reporting block

    # TODO eventually we want to remove this, when reports become fully asynchronous
    # The UI should be retrieving the report elsewhere via the download_report() method call
    return Response(
        stream_with_context(
            generate_notifications_csv(
                service_id=service_id,
                job_id=None,
                status=filter_args.get("status"),
                page=request.args.get("page", 1),
                page_size=10000,
                format_for_csv=True,
                template_type=filter_args.get("message_type"),
                limit_days=service_data_retention_days,
            )
        ),
        mimetype="text/csv",
        headers={
            "Content-Disposition": 'inline; filename="{} - {} - {} report.csv"'.format(
                file_time,
                filter_args["message_type"][0],
                current_service.name,
            )
        },
    )
