from datetime import datetime

from flask import render_template, request

from app import current_service
from app.main import main
from app.utils.pagination import generate_next_dict, generate_previous_dict
from app.utils.user import user_has_permissions

MAX_FILE_UPLOAD_SIZE = 2 * 1024 * 1024  # 2MB


@main.route("/services/<uuid:service_id>/uploads")
@user_has_permissions()
def uploads(service_id):
    # No tests have been written, this has been quickly prepared for user research.
    # It's also very like that a new view will be created to show uploads.
    uploads = current_service.get_page_of_uploads(page=request.args.get("page"))

    prev_page = None
    if uploads.prev_page:
        prev_page = generate_previous_dict(
            "main.uploads", service_id, uploads.current_page
        )
    next_page = None
    if uploads.next_page:
        next_page = generate_next_dict("main.uploads", service_id, uploads.current_page)

    if uploads.current_page == 1:
        listed_uploads = current_service.scheduled_jobs + uploads
    else:
        listed_uploads = uploads

    return render_template(
        "views/jobs/jobs.html",
        jobs=listed_uploads,
        prev_page=prev_page,
        next_page=next_page,
        now=datetime.utcnow().isoformat(),
    )
