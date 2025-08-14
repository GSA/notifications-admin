from flask import abort, render_template, request, url_for

from app import current_service, job_api_client
from app.enums import NotificationStatus, ServicePermission
from app.formatters import get_time_left
from app.main import main
from app.utils.pagination import (
    generate_next_dict,
    generate_pagination_pages,
    generate_previous_dict,
    get_page_from_request,
)
from app.utils.user import user_has_permissions


def get_report_info(service_id, report_name):
    from app.s3_client import check_s3_file_exists
    from app.s3_client.s3_csv_client import get_csv_upload

    try:
        obj = get_csv_upload(service_id, report_name)
        if check_s3_file_exists(obj):
            size_bytes = obj.content_length
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
            return {"available": True, "size": size_str}
    except Exception:
        pass
    return {"available": False, "size": None}


def get_download_availability(service_id):
    report_1_day = get_report_info(service_id, "1-day-report")
    report_3_day = get_report_info(service_id, "3-day-report")
    report_5_day = get_report_info(service_id, "5-day-report")
    report_7_day = get_report_info(service_id, "7-day-report")

    return {
        "report_1_day": report_1_day,
        "report_3_day": report_3_day,
        "report_5_day": report_5_day,
        "report_7_day": report_7_day,
    }


def get_download_links(message_type):
    time_periods = ["one_day", "three_day", "five_day", "seven_day"]
    links = {}

    for period in time_periods:
        links[f"download_link_{period}"] = url_for(
            ".download_notifications_csv",
            service_id=current_service.id,
            message_type=message_type,
            status=request.args.get("status"),
            number_of_days=period,
        )
    return links


def get_filtered_jobs(service_id, page):
    filter_type = request.args.get("filter")

    limit_days = None
    if filter_type == "24hours":
        limit_days = 1
    elif filter_type == "3days":
        limit_days = 3
    elif filter_type == "7days":
        limit_days = 7

    if limit_days:
        return job_api_client.get_page_of_jobs(
            service_id, page=page, limit_days=limit_days, use_processing_time=True
        )
    else:
        return job_api_client.get_page_of_jobs(service_id, page=page)


@main.route("/activity/services/<uuid:service_id>")
@user_has_permissions(ServicePermission.VIEW_ACTIVITY)
def all_jobs_activity(service_id):
    service_data_retention_days = 7
    page = get_page_from_request()

    jobs = get_filtered_jobs(service_id, page)

    all_jobs_dict = generate_job_dict(jobs)
    prev_page, next_page, pagination = handle_pagination(jobs, service_id, page)
    message_type = ("sms",)
    download_availability = get_download_availability(service_id)
    download_links = get_download_links(message_type)

    return render_template(
        "views/activity/all-activity.html",
        all_jobs_dict=all_jobs_dict,
        service_data_retention_days=service_data_retention_days,
        next_page=next_page,
        prev_page=prev_page,
        pagination=pagination,
        total_jobs=jobs.get("total", 0),
        **download_availability,
        **download_links,
    )


def handle_pagination(jobs, service_id, page):
    if page is None:
        abort(404, "Invalid page argument ({}).".format(request.args.get("page")))

    url_args = {}
    if request.args.get("filter"):
        url_args["filter"] = request.args.get("filter")

    prev_page = (
        generate_previous_dict("main.all_jobs_activity", service_id, page, url_args)
        if page > 1
        else None
    )
    total_items = jobs.get("total", 0)
    page_size = jobs.get("page_size", 50)
    total_pages = (total_items + page_size - 1) // page_size
    has_next_link = jobs.get("links", {}).get("next") is not None
    next_page = (
        generate_next_dict("main.all_jobs_activity", service_id, page, url_args)
        if has_next_link and total_items > 50 and page < total_pages
        else None
    )
    pagination = generate_pagination_pages(
        jobs.get("total", {}), jobs.get("page_size", {}), page
    )
    return prev_page, next_page, pagination


def get_job_statistics(job, status):
    statistics = job.get("statistics", [])
    for stat in statistics:
        if stat.get("status") == status:
            return stat.get("count")
    return None


def create_job_dict_entry(job):
    job_id = job.get("id")
    can_download = get_time_left(job.get("created_at")) != "Data no longer available"
    activity_time = job.get("processing_started") or job.get("created_at")

    return {
        "job_id": job_id,
        "can_download": can_download,
        "download_link": (
            url_for(".view_job_csv", service_id=current_service.id, job_id=job_id)
            if can_download
            else None
        ),
        "view_job_link": url_for(
            ".view_job", service_id=current_service.id, job_id=job_id
        ),
        "activity_time": activity_time,
        "created_by": job.get("created_by"),
        "template_name": job.get("template_name"),
        "delivered_count": get_job_statistics(job, NotificationStatus.DELIVERED),
        "failed_count": get_job_statistics(job, NotificationStatus.FAILED),
    }


def generate_job_dict(jobs):
    if not jobs or not jobs.get("data"):
        return []
    return [create_job_dict_entry(job) for job in jobs["data"]]
