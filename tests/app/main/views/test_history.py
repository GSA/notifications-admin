import pytest
from freezegun import freeze_time

from tests.conftest import SERVICE_ONE_ID, normalize_spaces


@pytest.mark.parametrize(
    ("extra_args", "expected_headings_and_events"),
    [
        (
            {},
            [
                (
                    "12 December 2012",
                    (
                        "Test User 13:13 "
                        "Renamed this service from ‘Before lunch’ to ‘After lunch’ "
                        "Test User 12:12 "
                        "Renamed this service from ‘Example service’ to ‘Before lunch’"
                    ),
                ),
                (
                    "11 November 2012",
                    ("Test User 12:12 " "Revoked the ‘Bad key’ API key"),
                ),
                (
                    "11 November",
                    ("Test User 11:11 " "Created an API key called ‘Bad key’"),
                ),
                (
                    "10 October 2010",
                    (
                        "Test User 11:10 "
                        "Created an API key called ‘Good key’ "
                        "Test User 10:09 "
                        "Created an API key called ‘Key event returned in non-chronological order’ "
                        "Test User 02:01 "
                        "Created this service and called it ‘Example service’"
                    ),
                ),
            ],
        ),
        (
            {"selected": "api"},
            [
                (
                    "11 November 2012",
                    ("Test User 12:12 " "Revoked the ‘Bad key’ API key"),
                ),
                (
                    "11 November",
                    ("Test User 11:11 " "Created an API key called ‘Bad key’"),
                ),
                (
                    "10 October 2010",
                    (
                        "Test User 11:10 "
                        "Created an API key called ‘Good key’ "
                        "Test User 10:09 "
                        "Created an API key called ‘Key event returned in non-chronological order’"
                    ),
                ),
            ],
        ),
        (
            {"selected": "service"},
            [
                (
                    "12 December 2012",
                    (
                        "Test User 13:13 "
                        "Renamed this service from ‘Before lunch’ to ‘After lunch’ "
                        "Test User 12:12 "
                        "Renamed this service from ‘Example service’ to ‘Before lunch’"
                    ),
                ),
                (
                    "10 October 2010",
                    (
                        "Test User 02:01 "
                        "Created this service and called it ‘Example service’"
                    ),
                ),
            ],
        ),
    ],
)
@freeze_time("2012-01-01 01:01:01")
def test_history(
    client_request,
    mock_get_service_history,
    mock_get_users_by_service,
    extra_args,
    expected_headings_and_events,
):
    page = client_request.get("main.history", service_id=SERVICE_ONE_ID, **extra_args)

    assert page.select_one("h1").text == "Audit events"

    headings = page.select("main h2.heading-small")
    events = page.select("main ul.bottom-gutter")

    assert len(headings) == len(events) == len(expected_headings_and_events)

    for index, expected in enumerate(expected_headings_and_events):
        assert (
            normalize_spaces(headings[index].text),
            normalize_spaces(events[index].text),
        ) == expected
