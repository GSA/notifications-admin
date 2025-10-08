# -*- coding: utf-8 -*-
# from functools import partial

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

# from flask_login import current_user
from markupsafe import Markup

from app import (  # notification_api_client,; service_api_client,
    current_service,
    format_datetime_table,
)

# from app.enums import NotificationStatus, NotificationType, ServicePermission
from app.enums import ServicePermission
from app.formatters import get_time_left, message_count_noun
from app.main import main

# from app.main.forms import SearchNotificationsForm
from app.models.job import Job
from app.utils import parse_filter_args, set_status_filters
from app.utils.csv import generate_notifications_csv

# from app.utils.pagination import (
#     generate_next_dict,
#     generate_previous_dict,
#     get_page_from_request,
# )
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


# @main.route("/services/<uuid:service_id>/notifications", methods=["GET", "POST"])
# @main.route(
#     "/services/<uuid:service_id>/notifications/<template_type:message_type>",
#     methods=["GET", "POST"],
# )
# @user_has_permissions()
# def view_notifications(service_id, message_type=None):
#     return render_template(
#         "views/notifications.html",
#         partials=get_notifications(service_id, message_type),
#         message_type=message_type,
#         status=request.args.get("status") or "sending,delivered,failed",
#         page=request.args.get("page", 1),
#         search_form=SearchNotificationsForm(
#             message_type=message_type,
#             to=request.form.get("to"),
#         ),
#         things_you_can_search_by={
#             "email": ["email address"],
#             "sms": ["phone number"],
#             None: ["recipient"],
#         }.get(message_type)
#         + {
#             True: ["reference"],
#             False: [],
#         }.get(bool(current_service.api_keys)),
#         download_link_one_day=url_for(
#             ".download_notifications_csv",
#             service_id=current_service.id,
#             message_type=message_type,
#             status=request.args.get("status"),
#             number_of_days="one_day",
#         ),
#         download_link_today=url_for(
#             ".download_notifications_csv",
#             service_id=current_service.id,
#             message_type=message_type,
#             status=request.args.get("status"),
#             number_of_days="today",
#         ),
#         download_link_three_day=url_for(
#             ".download_notifications_csv",
#             service_id=current_service.id,
#             message_type=message_type,
#             status=request.args.get("status"),
#             number_of_days="three_day",
#         ),
#         download_link_five_day=url_for(
#             ".download_notifications_csv",
#             service_id=current_service.id,
#             message_type=message_type,
#             status=request.args.get("status"),
#             number_of_days="five_day",
#         ),
#         download_link_seven_day=url_for(
#             ".download_notifications_csv",
#             service_id=current_service.id,
#             message_type=message_type,
#             status=request.args.get("status"),
#             number_of_days="seven_day",
#         ),
#     )


# @main.route("/services/<uuid:service_id>/notifications.json", methods=["GET", "POST"])
# @main.route(
#     "/services/<uuid:service_id>/notifications/<template_type:message_type>.json",
#     methods=["GET", "POST"],
# )
# @user_has_permissions()
# def get_notifications_as_json(service_id, message_type=None):
#     return jsonify(
#         get_notifications(
#             service_id, message_type, status_override=request.args.get("status")
#         )
#     )


# @main.route(
#     "/services/<uuid:service_id>/notifications.csv", endpoint="view_notifications_csv"
# )
# @main.route(
#     "/services/<uuid:service_id>/notifications/<template_type:message_type>.csv",
#     endpoint="view_notifications_csv",
# )
# @user_has_permissions()
# def get_notifications(service_id, message_type, status_override=None):  # noqa
#     # TODO get the api to return count of pages as well.
#     page = get_page_from_request()
#     if page is None:
#         abort(404, "Invalid page argument ({}).".format(request.args.get("page")))
#     filter_args = parse_filter_args(request.args)
#     filter_args["status"] = set_status_filters(filter_args)
#     service_data_retention_days = None
#     search_term = request.form.get("to", "")
#     if message_type is not None:
#         service_data_retention_days = current_service.get_days_of_retention(
#             message_type, number_of_days="seven_day"
#         )
#
#     if request.path.endswith("csv") and current_user.has_permissions(
#         ServicePermission.VIEW_ACTIVITY
#     ):
#         return Response(
#             generate_notifications_csv(
#                 service_id=service_id,
#                 page=page,
#                 page_size=5000,
#                 template_type=[message_type],
#                 status=filter_args.get("status"),
#                 limit_days=service_data_retention_days,
#             ),
#             mimetype="text/csv",
#             headers={"Content-Disposition": 'inline; filename="notifications.csv"'},
#         )
#     notifications = notification_api_client.get_notifications_for_service(
#         service_id=service_id,
#         page=page,
#         template_type=[message_type] if message_type else [],
#         status=filter_args.get("status"),
#         limit_days=service_data_retention_days,
#         to=search_term,
#     )
#
#     notifications_list = notifications.get("notifications", [])
#
#     url_args = {"message_type": message_type, "status": request.args.get("status")}
#     prev_page = None
#     if "links" in notifications and notifications["links"].get("prev", None):
#         prev_page = generate_previous_dict(
#             "main.view_notifications", service_id, page, url_args=url_args
#         )
#     next_page = None
#
#     total_items = notifications.get("total", 0)
#     page_size = notifications.get("page_size", 50)
#     total_pages = (total_items + page_size - 1) // page_size
#     if (
#         "links" in notifications
#         and notifications["links"].get("next", None)
#         and total_items > 50
#         and page < total_pages
#     ):
#         next_page = generate_next_dict(
#             "main.view_notifications", service_id, page, url_args
#         )
#
#     if message_type:
#         download_link = url_for(
#             ".view_notifications_csv",
#             service_id=current_service.id,
#             message_type=message_type,
#             status=request.args.get("status"),
#         )
#     else:
#         download_link = None
#     return {
#         "service_data_retention_days": service_data_retention_days,
#         "counts": render_template(
#             "views/activity/counts.html",
#             status=request.args.get("status"),
#             status_filters=get_status_filters(
#                 current_service,
#                 message_type,
#                 service_api_client.get_service_statistics(
#                     service_id, limit_days=service_data_retention_days
#                 ),
#             ),
#         ),
#         "notifications": render_template(
#             "views/activity/notifications.html",
#             notifications=list(
#                 add_preview_of_content_to_notifications(notifications_list)
#             ),
#             page=page,
#             limit_days=service_data_retention_days,
#             prev_page=prev_page,
#             next_page=next_page,
#             show_pagination=(not search_term),
#             status=request.args.get("status"),
#             message_type=message_type,
#             download_link=download_link,
#             single_notification_url=partial(
#                 url_for,
#                 ".view_notification",
#                 service_id=current_service.id,
#             ),
#         ),
#     }


# def get_status_filters(service, message_type, statistics):
#     message_types = (
#         [message_type]
#         if message_type
#         else [NotificationType.EMAIL, NotificationType.SMS]
#     )
#
#     stats = {
#         NotificationStatus.REQUESTED: sum(
#             statistics[mt].get(NotificationStatus.REQUESTED, 0) for mt in message_types
#         ),
#         NotificationStatus.DELIVERED: sum(
#             statistics[mt].get(NotificationStatus.DELIVERED, 0) for mt in message_types
#         ),
#         NotificationStatus.FAILED: sum(
#             statistics[mt].get(NotificationStatus.FAILED, 0) for mt in message_types
#         ),
#     }
#
#     stats[NotificationStatus.PENDING] = (
#         stats[NotificationStatus.REQUESTED]
#         - stats[NotificationStatus.DELIVERED]
#         - stats[NotificationStatus.FAILED]
#     )
#
#     filters = [
#         (NotificationStatus.REQUESTED, "total", "sending,delivered,failed"),
#         (NotificationStatus.PENDING, "pending", "sending,pending"),
#         (NotificationStatus.DELIVERED, "delivered", "delivered"),
#         (NotificationStatus.FAILED, "failed", "failed"),
#     ]
#     return [
#         (
#             label,
#             option,
#             url_for(
#                 ".view_notifications",
#                 service_id=service.id,
#                 message_type=message_type,
#                 status=option,
#             ),
#             stats.get(key),
#         )
#         for key, label, option in filters
#     ]


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
