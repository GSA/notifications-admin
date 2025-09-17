# -*- coding: utf-8 -*-
import os
from functools import partial

from flask import (
    Response,
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    stream_with_context,
    url_for,
)
from flask_login import current_user
from markupsafe import Markup

from app import (
    current_service,
    format_datetime_table,
    notification_api_client,
    service_api_client,
)
from app.enums import JobStatus, NotificationStatus, ServicePermission
from app.formatters import get_time_left, message_count_noun
from app.main import main
from app.main.forms import SearchNotificationsForm
from app.models.job import Job
from app.utils import parse_filter_args, set_status_filters
from app.utils.csv import generate_notifications_csv
from app.utils.pagination import (
    generate_next_dict,
    generate_previous_dict,
    get_page_from_request,
)
from app.utils.user import user_has_permissions
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
    api_public_url = os.environ.get("API_PUBLIC_URL")

    return render_template(
        "views/jobs/job.html",
        api_public_url=api_public_url,
        FEATURE_SOCKET_ENABLED=current_app.config["FEATURE_SOCKET_ENABLED"],
        job=job,
        status=request.args.get("status", ""),
        updates_url=url_for(
            ".view_job_updates",
            service_id=service_id,
            job_id=job.id,
            status=request.args.get("status", ""),
        ),
        partials=get_job_partials(job),
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


@main.route("/services/<uuid:service_id>/jobs/<uuid:job_id>.json")
@user_has_permissions()
def view_job_updates(service_id, job_id):
    job = Job.from_id(job_id, service_id=service_id)

    return jsonify(**get_job_partials(job))


@main.route("/services/<uuid:service_id>/notifications", methods=["GET", "POST"])
@main.route(
    "/services/<uuid:service_id>/notifications/<template_type:message_type>",
    methods=["GET", "POST"],
)
@user_has_permissions()
def view_notifications(service_id, message_type=None):
    return render_template(
        "views/notifications.html",
        partials=get_notifications(service_id, message_type),
        message_type=message_type,
        status=request.args.get("status") or "sending,delivered,failed",
        page=request.args.get("page", 1),
        search_form=SearchNotificationsForm(
            message_type=message_type,
            to=request.form.get("to"),
        ),
        things_you_can_search_by={
            "email": ["email address"],
            "sms": ["phone number"],
            # We say recipient here because combining all 3 types, plus
            # reference gets too long for the hint text
            None: ["recipient"],
        }.get(message_type)
        + {
            True: ["reference"],
            False: [],
        }.get(bool(current_service.api_keys)),
        download_link_one_day=url_for(
            ".download_notifications_csv",
            service_id=current_service.id,
            message_type=message_type,
            status=request.args.get("status"),
            number_of_days="one_day",
        ),
        download_link_today=url_for(
            ".download_notifications_csv",
            service_id=current_service.id,
            message_type=message_type,
            status=request.args.get("status"),
            number_of_days="today",
        ),
        download_link_three_day=url_for(
            ".download_notifications_csv",
            service_id=current_service.id,
            message_type=message_type,
            status=request.args.get("status"),
            number_of_days="three_day",
        ),
        download_link_five_day=url_for(
            ".download_notifications_csv",
            service_id=current_service.id,
            message_type=message_type,
            status=request.args.get("status"),
            number_of_days="five_day",
        ),
        download_link_seven_day=url_for(
            ".download_notifications_csv",
            service_id=current_service.id,
            message_type=message_type,
            status=request.args.get("status"),
            number_of_days="seven_day",
        ),
    )


@main.route("/services/<uuid:service_id>/notifications.json", methods=["GET", "POST"])
@main.route(
    "/services/<uuid:service_id>/notifications/<template_type:message_type>.json",
    methods=["GET", "POST"],
)
@user_has_permissions()
def get_notifications_as_json(service_id, message_type=None):
    return jsonify(
        get_notifications(
            service_id, message_type, status_override=request.args.get("status")
        )
    )


@main.route(
    "/services/<uuid:service_id>/notifications.csv", endpoint="view_notifications_csv"
)
@main.route(
    "/services/<uuid:service_id>/notifications/<template_type:message_type>.csv",
    endpoint="view_notifications_csv",
)
@user_has_permissions()
def get_notifications(service_id, message_type, status_override=None):  # noqa
    # TODO get the api to return count of pages as well.
    page = get_page_from_request()
    if page is None:
        abort(404, "Invalid page argument ({}).".format(request.args.get("page")))
    filter_args = parse_filter_args(request.args)
    filter_args["status"] = set_status_filters(filter_args)
    service_data_retention_days = None
    search_term = request.form.get("to", "")
    if message_type is not None:
        service_data_retention_days = current_service.get_days_of_retention(
            message_type, number_of_days="seven_day"
        )

    if request.path.endswith("csv") and current_user.has_permissions(
        ServicePermission.VIEW_ACTIVITY
    ):
        return Response(
            generate_notifications_csv(
                service_id=service_id,
                page=page,
                page_size=5000,
                template_type=[message_type],
                status=filter_args.get("status"),
                limit_days=service_data_retention_days,
            ),
            mimetype="text/csv",
            headers={"Content-Disposition": 'inline; filename="notifications.csv"'},
        )
    notifications = notification_api_client.get_notifications_for_service(
        service_id=service_id,
        page=page,
        template_type=[message_type] if message_type else [],
        status=filter_args.get("status"),
        limit_days=service_data_retention_days,
        to=search_term,
    )
    url_args = {"message_type": message_type, "status": request.args.get("status")}
    prev_page = None
    if "links" in notifications and notifications["links"].get("prev", None):
        prev_page = generate_previous_dict(
            "main.view_notifications", service_id, page, url_args=url_args
        )
    next_page = None

    total_items = notifications.get("total", 0)
    page_size = notifications.get("page_size", 50)
    total_pages = (total_items + page_size - 1) // page_size
    if (
        "links" in notifications
        and notifications["links"].get("next", None)
        and total_items > 50
        and page < total_pages
    ):
        next_page = generate_next_dict(
            "main.view_notifications", service_id, page, url_args
        )

    if message_type:
        download_link = url_for(
            ".view_notifications_csv",
            service_id=current_service.id,
            message_type=message_type,
            status=request.args.get("status"),
        )
    else:
        download_link = None
    return {
        "service_data_retention_days": service_data_retention_days,
        "counts": render_template(
            "views/activity/counts.html",
            status=request.args.get("status"),
            status_filters=get_status_filters(
                current_service,
                message_type,
                service_api_client.get_service_statistics(
                    service_id, limit_days=service_data_retention_days
                ),
            ),
        ),
        "notifications": render_template(
            "views/activity/notifications.html",
            notifications=list(
                add_preview_of_content_to_notifications(notifications["notifications"])
            ),
            page=page,
            limit_days=service_data_retention_days,
            prev_page=prev_page,
            next_page=next_page,
            show_pagination=(not search_term),
            status=request.args.get("status"),
            message_type=message_type,
            download_link=download_link,
            single_notification_url=partial(
                url_for,
                ".view_notification",
                service_id=current_service.id,
            ),
        ),
    }


def get_status_filters(service, message_type, statistics):
    if message_type is None:
        stats = {
            "requested": sum(
                statistics[message_type]["requested"]
                for message_type in {"email", "sms"}
            ),
            NotificationStatus.DELIVERED: sum(
                statistics[message_type][NotificationStatus.DELIVERED]
                for message_type in {"email", "sms"}
            ),
            "failure": sum(
                statistics[message_type].get("failure", 0)
                for message_type in {"email", "sms"}
            ),
        }
    else:
        stats = statistics[message_type]

    # Map API keys to enum keys for consistency
    if stats.get("failure") is not None:
        stats[NotificationStatus.FAILED] = stats["failure"]
    if stats.get(NotificationStatus.DELIVERED) is not None:
        stats[NotificationStatus.DELIVERED] = stats[NotificationStatus.DELIVERED]

    stats[NotificationStatus.PENDING] = (
        stats["requested"]
        - stats[NotificationStatus.DELIVERED]
        - stats[NotificationStatus.FAILED]
    )

    filters = [
        # key, label, option
        ("requested", "total", "sending,delivered,failed"),
        (NotificationStatus.PENDING, "pending", "sending,pending"),
        (NotificationStatus.DELIVERED, "delivered", "delivered"),
        (NotificationStatus.FAILED, "failed", "failed"),
    ]
    return [
        # return list containing label, option, link, count
        (
            label,
            option,
            url_for(
                ".view_notifications",
                service_id=service.id,
                message_type=message_type,
                status=option,
            ),
            stats.get(key),
        )
        for key, label, option in filters
    ]


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


def get_job_partials(job):
    filter_args = parse_filter_args(request.args)
    filter_args["status"] = set_status_filters(filter_args)
    notifications = job.get_notifications(status=filter_args["status"])
    number_of_days = "seven_day"
    counts = render_template(
        "partials/count.html",
        counts=_get_job_counts(job),
        status=filter_args["status"],
        notifications_deleted=(
            job.status == JobStatus.FINISHED and not notifications["notifications"]
        ),
    )
    service_data_retention_days = current_service.get_days_of_retention(
        job.template_type, number_of_days
    )

    if request.referrer is not None:
        session["arrived_from_preview_page"] = ("check" in request.referrer) or (
            "help=0" in request.referrer
        )
    else:
        session["arrived_from_preview_page"] = False

    arrived_from_preview_page_url = session.get("arrived_from_preview_page", False)

    return {
        "counts": counts,
        "notifications": render_template(
            "partials/jobs/notifications.html",
            notifications=list(
                add_preview_of_content_to_notifications(notifications["notifications"])
            ),
            more_than_one_page=bool(notifications.get("links", {}).get("next")),
            download_link=url_for(
                ".view_job_csv",
                service_id=current_service.id,
                job_id=job.id,
                status=request.args.get("status"),
            ),
            time_left=get_time_left(
                job.created_at, service_data_retention_days=service_data_retention_days
            ),
            job=job,
            service_data_retention_days=service_data_retention_days,
        ),
        "status": render_template(
            "partials/jobs/status.html",
            job=job,
            arrived_from_preview_page_url=arrived_from_preview_page_url,
        ),
    }


def add_preview_of_content_to_notifications(notifications):
    for notification in notifications:
        yield (
            dict(
                preview_of_content=get_preview_of_content(notification), **notification
            )
        )


def get_preview_of_content(notification):
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
