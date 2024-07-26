from flask import request, url_for


def get_page_from_request():
    if "page" in request.args:
        try:
            return int(request.args["page"])
        except ValueError:
            return None
    else:
        return 1


def generate_previous_dict(view, service_id, page, url_args=None):
    return generate_previous_next_dict(
        view, service_id, page - 1, "Previous page", url_args or {}
    )


def generate_next_dict(view, service_id, page, url_args=None):
    return generate_previous_next_dict(
        view, service_id, page + 1, "Next page", url_args or {}
    )


def generate_previous_next_dict(view, service_id, page, title, url_args):
    return {
        "url": url_for(view, service_id=service_id, page=page, **url_args),
        "title": title,
        "label": "page {}".format(page),
    }


def generate_pagination_pages(total_items, page_size, current_page):
    total_pages = (total_items + page_size - 1) // page_size
    pagination = {"current": current_page, "pages": [], "last": total_pages}
    if total_pages <= 9:
        pagination["pages"] = list(range(1, total_pages + 1))
    else:
        start_page = max(1, min(current_page - 4, total_pages - 8))
        end_page = min(start_page + 8, total_pages)
        pagination["pages"] = list(range(start_page, end_page + 1))
    return pagination
