# -*- coding: utf-8 -*-

from flask import (
    Response,
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    stream_with_context,
    url_for,
)
from markupsafe import Markup

from app import current_service, format_datetime_table
from app.enums import ServicePermission
from app.formatters import get_time_left, message_count_noun
from app.main import main
from app.models.job import Job
from app.utils import parse_filter_args, set_status_filters
from app.utils.csv import generate_notifications_csv
from app.utils.user import user_has_permissions
from notifications_python_client.errors import HTTPError
from notifications_utils.template import EmailPreviewTemplate, SMSBodyPreviewTemplate


@main.route("/services/<uuid:service_id>/jobs")
@user_has_permissions()
def view_jobs(service_id):
    return redirect(
        url_for(
            "main.uploads",
            service_id=current_service.id,
        )
    )


@main.route("/services/<uuid:service_id>/jobs/<uuid:job_id>")
@user_has_permissions()
def view_job(service_id, job_id):
    job = Job.from_id(job_id, service_id=current_service.id)
    if job.cancelled:
        abort(404)

    filter_args = parse_filter_args(request.args)
    filter_args["status"] = set_status_filters(filter_args)

    notifications = None
    more_than_one_page = False
    if job.finished_processing:
        notifications_data = job.get_notifications(status=filter_args["status"])
        notifications = list(
            add_preview_of_content_to_notifications(
                notifications_data.get("notifications", [])
            )
        )
        more_than_one_page = bool(notifications_data.get("links", {}).get("next"))

    return render_template(
        "views/jobs/job.html",
        job=job,
        status=request.args.get("status", ""),
        counts=_get_job_counts(job),
        notifications=notifications,
        more_than_one_page=more_than_one_page,
        uploaded_file_name=job.original_file_name,
        time_left=get_time_left(job.created_at),
        service_data_retention_days=current_service.get_days_of_retention(
            job.template_type, number_of_days="seven_day"
        ),
        download_link=(
            url_for(
                ".view_job_csv",
                service_id=service_id,
                job_id=job_id,
                status=request.args.get("status"),
            )
            if job.finished_processing
            else None
        ),
    )


@main.route("/services/<uuid:service_id>/jobs/<uuid:job_id>.csv")
@user_has_permissions(ServicePermission.VIEW_ACTIVITY)
def view_job_csv(service_id, job_id):
    job = Job.from_id(job_id, service_id=service_id)
    filter_args = parse_filter_args(request.args)
    filter_args["status"] = set_status_filters(filter_args)

    return Response(
        stream_with_context(
            generate_notifications_csv(
                service_id=service_id,
                job_id=job_id,
                status=filter_args.get("status"),
                page=request.args.get("page", 1),
                page_size=5000,
                format_for_csv=True,
                template_type=job.template_type,
            )
        ),
        mimetype="text/csv",
        headers={
            "Content-Disposition": 'inline; filename="{} - {}.csv"'.format(
                job.template["name"], format_datetime_table(job.created_at)
            )
        },
    )


@main.route("/services/<uuid:service_id>/jobs/<uuid:job_id>", methods=["POST"])
@user_has_permissions(ServicePermission.SEND_MESSAGES)
def cancel_job(service_id, job_id):
    Job.from_id(job_id, service_id=service_id).cancel()
    return redirect(url_for("main.service_dashboard", service_id=service_id))


@main.route("/services/<uuid:service_id>/jobs/<uuid:job_id>/status.json")
@user_has_permissions()
def view_job_status_poll(service_id, job_id):
    from app.notify_client.job_api_client import job_api_client

    try:
        api_response = job_api_client.get_job_status(service_id, job_id)
    except HTTPError as e:
        current_app.logger.error(
            f"API error fetching job status: {e.status_code} - {e.message}"
        )
        if e.status_code == 404:
            abort(404)
        elif e.status_code >= 500:
            abort(503, "Service temporarily unavailable")
        else:
            abort(500, "Failed to fetch job status")

    response_data = {
        "total": api_response.get("total", 0),
        "delivered": api_response.get("delivered", 0),
        "failed": api_response.get("failed", 0),
        "pending": api_response.get("pending", 0),
        "finished": api_response.get("finished", False),
    }

    return jsonify(response_data)


@main.route("/services/<uuid:service_id>/jobs/<uuid:job_id>/notifications-table")
@user_has_permissions()
def view_job_notifications_table(service_id, job_id):
    """Endpoint that returns only the notifications table HTML fragment."""
    job = Job.from_id(job_id, service_id=current_service.id)

    if job.cancelled or not job.finished_processing:
        return "", 204

    filter_args = parse_filter_args(request.args)
    filter_args["status"] = set_status_filters(filter_args)

    notifications_data = job.get_notifications(status=filter_args["status"])
    notifications = list(
        add_preview_of_content_to_notifications(
            notifications_data.get("notifications", [])
        )
    )
    more_than_one_page = bool(notifications_data.get("links", {}).get("next"))

    return render_template(
        "partials/jobs/notifications.html",
        job=job,
        notifications=notifications,
        more_than_one_page=more_than_one_page,
        uploaded_file_name=job.original_file_name,
        time_left=get_time_left(job.created_at),
        service_data_retention_days=current_service.get_days_of_retention(
            job.template_type, number_of_days="seven_day"
        ),
        download_link=url_for(
            ".view_job_csv",
            service_id=current_service.id,
            job_id=job.id,
        ),
    )


def _get_job_counts(job):
    job_type = job.template_type
    return [
        (
            label,
            query_param,
            url_for(
                ".view_job",
                service_id=job.service,
                job_id=job.id,
                status=query_param,
            ),
            count,
        )
        for label, query_param, count in [
            [
                Markup(
                    f"""total<span class="usa-sr-only">
                    {"text message" if job_type == "sms" else job_type}s</span>"""
                ),  # nosec
                "",
                job.notification_count,
            ],
            [
                Markup(
                    f"""pending<span class="usa-sr-only">
                    {message_count_noun(job.notifications_sending, job_type)}</span>"""
                ),  # nosec
                "pending",
                job.notifications_sending,
            ],
            [
                Markup(
                    f"""delivered<span class="usa-sr-only">
                    {message_count_noun(job.notifications_delivered, job_type)}</span>"""
                ),  # nosec
                "delivered",
                job.notifications_delivered,
            ],
            [
                Markup(
                    f"""failed<span class="usa-sr-only">
                    {message_count_noun(job.notifications_failed, job_type)}</span>"""
                ),  # nosec
                "failed",
                job.notifications_failed,
            ],
        ]
    ]


def add_preview_of_content_to_notifications(notifications):
    for notification in notifications:
        if "template" not in notification and "template_name" in notification:
            notification["template"] = {
                "name": notification.get("template_name", ""),
                "template_type": "sms",
                "content": notification.get("template_name", ""),
            }

        if "content" not in notification:
            notification["content"] = notification.get("template_name", "")

        yield (
            dict(
                preview_of_content=get_preview_of_content(notification), **notification
            )
        )


def get_preview_of_content(notification):
    if "template" not in notification:
        return notification.get("template_name", "")

    if notification["template"].get("redact_personalisation"):
        notification["personalisation"] = {}

    if notification["template"]["template_type"] == "sms":
        return str(
            SMSBodyPreviewTemplate(
                notification["template"],
                notification["personalisation"],
            )
        )

    if notification["template"]["template_type"] == "email":
        return Markup(
            EmailPreviewTemplate(
                notification["template"],
                notification["personalisation"],
                redact_missing_personalisation=True,
            ).subject
        )  # nosec
