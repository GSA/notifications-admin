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
    pagination = {
        'current': current_page,
        'pages': [],
        'last': total_pages
    }
    if total_pages <= 4:
        pagination['pages'] = list(range(1, total_pages + 1))
    else:
        if current_page <= 3:
            pagination['pages'] = [1, 2, 3, total_pages]
        else:
            pagination['pages'] = [1, current_page - 1, current_page, current_page + 1, total_pages]
    return pagination
