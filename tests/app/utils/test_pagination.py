import pytest

from app.utils.pagination import (
    generate_next_dict,
    generate_pagination_pages,
    generate_previous_dict,
)


def test_generate_previous_dict(client_request):
    result = generate_previous_dict("main.view_jobs", "foo", 2, {})
    assert "page=1" in result["url"]
    assert result["title"] == "Previous page"
    assert result["label"] == "page 1"


def test_generate_next_dict(client_request):
    result = generate_next_dict("main.view_jobs", "foo", 2, {})
    assert "page=3" in result["url"]
    assert result["title"] == "Next page"
    assert result["label"] == "page 3"


def test_generate_previous_next_dict_adds_other_url_args(client_request):
    result = generate_next_dict("main.view_jobs", "foo", 2, {"status": "pending"})
    assert "status=pending" in result["url"]


@pytest.mark.parametrize(
    ("total_items", "page_size", "current_page", "expected"),
    [
        (100, 50, 1, {"current": 1, "pages": [1, 2], "last": 2}),
        (450, 50, 1, {"current": 1, "pages": [1, 2, 3, 4, 5, 6, 7, 8, 9], "last": 9}),
        (500, 50, 1, {"current": 1, "pages": [1, 2, 3, 4, 5, 6, 7, 8, 9], "last": 10}),
        (500, 50, 5, {"current": 5, "pages": [1, 2, 3, 4, 5, 6, 7, 8, 9], "last": 10}),
        (500, 50, 6, {"current": 6, "pages": [2, 3, 4, 5, 6, 7, 8, 9, 10], "last": 10}),
        (
            500,
            50,
            10,
            {"current": 10, "pages": [2, 3, 4, 5, 6, 7, 8, 9, 10], "last": 10},
        ),
        (
            950,
            50,
            15,
            {"current": 15, "pages": [11, 12, 13, 14, 15, 16, 17, 18, 19], "last": 19},
        ),
    ],
)
def test_generate_pagination_pages(total_items, page_size, current_page, expected):
    result = generate_pagination_pages(total_items, page_size, current_page)
    assert result == expected
