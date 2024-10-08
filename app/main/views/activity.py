from flask import abort, render_template, request, url_for

from app import current_service, job_api_client
from app.formatters import convert_time_unixtimestamp, get_time_left
from app.main import main
from app.utils.pagination import (
    generate_next_dict,
    generate_pagination_pages,
    generate_previous_dict,
    get_page_from_request,
)
from app.utils.user import user_has_permissions


@main.route("/activity/services/<uuid:service_id>")
@user_has_permissions("view_activity")
def all_jobs_activity(service_id):
    service_data_retention_days = 7
    page = get_page_from_request()
    jobs = job_api_client.get_page_of_jobs(service_id, page=page)
    all_jobs_dict = generate_job_dict(jobs)
    prev_page, next_page, pagination = handle_pagination(jobs, service_id, page)
    message_type = ("sms",)
    return render_template(
        "views/activity/all-activity.html",
        all_jobs_dict=all_jobs_dict,
        service_data_retention_days=service_data_retention_days,
        next_page=next_page,
        prev_page=prev_page,
        pagination=pagination,
        download_link_one_day=url_for(
            ".download_notifications_csv",
            service_id=current_service.id,
            message_type=message_type,
            status=request.args.get("status"),
            number_of_days="one_day",
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


def handle_pagination(jobs, service_id, page):
    if page is None:
        abort(404, "Invalid page argument ({}).".format(request.args.get("page")))
    prev_page = (
        generate_previous_dict("main.all_jobs_activity", service_id, page)
        if page > 1
        else None
    )
    next_page = (
        generate_next_dict("main.all_jobs_activity", service_id, page)
        if jobs.get("links", {}).get("next")
        else None
    )
    pagination = generate_pagination_pages(
        jobs.get("total", {}), jobs.get("page_size", {}), page
    )
    return prev_page, next_page, pagination


def generate_job_dict(jobs):
    return [
        {
            "job_id": job["id"],
            "time_left": get_time_left(job["created_at"]),
            "download_link": url_for(
                ".view_job_csv", service_id=current_service.id, job_id=job["id"]
            ),
            "view_job_link": url_for(
                ".view_job", service_id=current_service.id, job_id=job["id"]
            ),
            "created_at": job["created_at"],
            "time_sent_data_value": convert_time_unixtimestamp(
                job["processing_finished"]
                if job["processing_finished"]
                else (
                    job["processing_started"]
                    if job["processing_started"]
                    else job["created_at"]
                )
            ),
            "processing_finished": job["processing_finished"],
            "processing_started": job["processing_started"],
            "created_by": job["created_by"],
            "template_name": job["template_name"],
            "delivered_count": next(
                (
                    stat["count"]
                    for stat in job.get("statistics", [])
                    if stat["status"] == "delivered"
                ),
                None,
            ),
            "failed_count": next(
                (
                    stat["count"]
                    for stat in job.get("statistics", [])
                    if stat["status"] == "failed"
                ),
                None,
            ),
        }
        for job in jobs["data"]
    ]
