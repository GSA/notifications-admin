import copy
import json
from datetime import datetime

import pytest
from flask import Flask, url_for
from flask_socketio import SocketIOTestClient
from freezegun import freeze_time

from app import create_app, socketio
from app.main.views.dashboard import (
    aggregate_notifications_stats,
    aggregate_status_types,
    aggregate_template_usage,
    format_monthly_stats_to_list,
    get_dashboard_totals,
    get_tuples_of_financial_years,
)
from tests import (
    organization_json,
    service_json,
    validate_route_permission,
    validate_route_permission_with_client,
)
from tests.conftest import (
    ORGANISATION_ID,
    SERVICE_ONE_ID,
    SERVICE_TWO_ID,
    create_active_caseworking_user,
    create_active_user_view_permissions,
    normalize_spaces,
)

FAKE_ONE_OFF_NOTIFICATION = {
    "links": {},
    "notifications": [
        {
            "api_key": None,
            "billable_units": 0,
            "carrier": None,
            "client_reference": None,
            "created_at": "2023-12-14T20:35:55+00:00",
            "created_by": {
                "email_address": "grsrbsrgsrf@fake.gov",
                "id": "de059e0a-42e5-48bb-939e-4f76804ab739",
                "name": "mocked_user",
            },
            "document_download_count": None,
            "id": "a3442b43-0ba1-4854-9e0a-d2fba1cc9b81",
            "international": False,
            "job": {
                "id": "55b242b5-9f62-4271-aff7-039e9c320578",
                "original_file_name": "1127b78e-a4a8-4b70-8f4f-9f4fbf03ece2.csv",
            },
            "job_row_number": 0,
            "key_name": None,
            "key_type": "normal",
            "normalised_to": "+16615555555",
            "notification_type": "sms",
            "personalisation": {
                "dayofweek": "2",
                "favecolor": "3",
                "phonenumber": "+16615555555",
            },
            "phone_prefix": "1",
            "provider_response": None,
            "rate_multiplier": 1.0,
            "reference": None,
            "reply_to_text": "development",
            "sent_at": None,
            "sent_by": None,
            "service": "f62d840f-8bcb-4b36-b959-4687e16dd1a1",
            "status": "created",
            "template": {
                "content": "((day of week)) and ((fave color))",
                "id": "bd9caa7e-00ee-4c5a-839e-10ae1a7e6f73",
                "name": "Template Testing",
                "redact_personalisation": False,
                "subject": None,
                "template_type": "sms",
                "version": 1,
            },
            "to": "+16615555555",
            "updated_at": None,
        }
    ],
    "page_size": 50,
    "total": 1,
}

MOCK_JOBS = {
    "data": [
        {
            "archived": False,
            "created_at": "2024-01-04T20:43:52+00:00",
            "created_by": {
                "id": "mocked_user_id",
                "name": "mocked_user",
            },
            "id": "55b242b5-9f62-4271-aff7-039e9c320578",
            "job_status": "finished",
            "notification_count": 1,
            "original_file_name": "mocked_file.csv",
            "processing_finished": "2024-01-25T23:02:25+00:00",
            "processing_started": "2024-01-25T23:02:24+00:00",
            "scheduled_for": None,
            "service": "21b3ee3d-1cb0-4666-bfa0-9c5ac26d3fe3",
            "service_name": {"name": "Mock Texting Service"},
            "statistics": [{"count": 1, "status": "sending"}],
            "template": "6a456418-498c-4c86-b0cd-9403c14a216c",
            "template_name": "Mock Template Name",
            "template_type": "sms",
            "template_version": 3,
            "updated_at": "2024-01-25T23:02:25+00:00",
        }
    ]
}

MOCK_JOBS_AND_NOTIFICATIONS = [
    {
        "created_at": MOCK_JOBS["data"][0]["created_at"],
        "created_by": MOCK_JOBS["data"][0]["created_by"],
        "download_link": "/services/21b3ee3d-1cb0-4666-bfa0-9c5ac26d3fe3/jobs/463b5ecb-4e32-43e5-aa90-0234d19fceaa.csv",
        "job_id": "55b242b5-9f62-4271-aff7-039e9c320578",
        "notification_count": MOCK_JOBS["data"][0]["notification_count"],
        "notifications": FAKE_ONE_OFF_NOTIFICATION["notifications"],
        "time_left": "Data available for 7 days",
        "view_job_link": "/services/21b3ee3d-1cb0-4666-bfa0-9c5ac26d3fe3/jobs/463b5ecb-4e32-43e5-aa90-0234d19fceaa",
    },
]

stub_template_stats = [
    {
        "template_type": "sms",
        "template_name": "one",
        "template_id": "id-1",
        "status": "created",
        "count": 50,
    },
    {
        "template_type": "email",
        "template_name": "two",
        "template_id": "id-2",
        "status": "created",
        "count": 100,
    },
    {
        "template_type": "email",
        "template_name": "two",
        "template_id": "id-2",
        "status": "technical-failure",
        "count": 100,
    },
    {
        "template_type": "sms",
        "template_name": "one",
        "template_id": "id-1",
        "status": "delivered",
        "count": 50,
    },
]


@pytest.mark.parametrize(
    "user",
    [
        create_active_user_view_permissions(),
        create_active_caseworking_user(),
    ],
)
def test_redirect_from_old_dashboard(
    client_request,
    user,
    mocker,
):
    mocker.patch("app.user_api_client.get_user", return_value=user)
    expected_location = "/services/{}".format(SERVICE_ONE_ID)

    client_request.get_url(
        "/services/{}/dashboard".format(SERVICE_ONE_ID),
        _expected_redirect=expected_location,
    )

    assert expected_location == url_for(
        "main.service_dashboard", service_id=SERVICE_ONE_ID
    )


def test_redirect_caseworkers_to_templates(
    client_request,
    mocker,
    active_caseworking_user,
):
    client_request.login(active_caseworking_user)
    client_request.get(
        "main.service_dashboard",
        service_id=SERVICE_ONE_ID,
        _expected_status=302,
        _expected_redirect=url_for(
            "main.choose_template",
            service_id=SERVICE_ONE_ID,
        ),
    )


def test_get_started(
    client_request,
    mocker,
    mock_get_service_templates_when_no_templates_exist,
    mock_has_no_jobs,
    mock_get_service_statistics,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    mocker.patch(
        "app.template_statistics_client.get_template_statistics_for_service",
        return_value=copy.deepcopy(stub_template_stats),
    )
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )
    page = client_request.get(
        "main.service_dashboard",
        service_id=SERVICE_ONE_ID,
    )

    mock_get_service_templates_when_no_templates_exist.assert_called_once_with(
        SERVICE_ONE_ID
    )
    assert "Get started" in page.text


def test_get_started_is_hidden_once_templates_exist(
    client_request,
    mocker,
    mock_get_service_templates,
    mock_has_no_jobs,
    mock_get_service_statistics,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    mocker.patch(
        "app.template_statistics_client.get_template_statistics_for_service",
        return_value=copy.deepcopy(stub_template_stats),
    )
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )
    page = client_request.get(
        "main.service_dashboard",
        service_id=SERVICE_ONE_ID,
    )

    mock_get_service_templates.assert_called_once_with(SERVICE_ONE_ID)
    assert not page.find("h2", string="Get started")


def test_inbound_messages_not_visible_to_service_without_permissions(
    client_request,
    mocker,
    service_one,
    mock_get_service_templates_when_no_templates_exist,
    mock_has_no_jobs,
    mock_get_service_statistics,
    mock_get_template_statistics,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    service_one["permissions"] = []
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )
    page = client_request.get(
        "main.service_dashboard",
        service_id=SERVICE_ONE_ID,
    )

    assert not page.select(".big-number-meta-wrapper")
    assert mock_get_inbound_sms_summary.called is False


def test_inbound_messages_shows_count_of_messages_when_there_are_messages(
    client_request,
    mocker,
    service_one,
    mock_get_service_templates_when_no_templates_exist,
    mock_get_jobs,
    mock_get_scheduled_job_stats,
    mock_get_service_statistics,
    mock_get_template_statistics,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    service_one["permissions"] = ["inbound_sms"]
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )
    page = client_request.get(
        "main.service_dashboard",
        service_id=SERVICE_ONE_ID,
    )
    mock_get_jobs.assert_called_with(SERVICE_ONE_ID)
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    banner = page.select("a.banner-dashboard")[1]
    assert (
        normalize_spaces(banner.text)
        == "9,999 text messages received latest message just now"
    )
    assert banner["href"] == url_for("main.inbox", service_id=SERVICE_ONE_ID)


def test_inbound_messages_shows_count_of_messages_when_there_are_no_messages(
    client_request,
    mocker,
    service_one,
    mock_get_service_templates_when_no_templates_exist,
    mock_get_jobs,
    mock_get_scheduled_job_stats,
    mock_get_service_statistics,
    mock_get_template_statistics,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary_with_no_messages,
):
    service_one["permissions"] = ["inbound_sms"]
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )
    page = client_request.get(
        "main.service_dashboard",
        service_id=SERVICE_ONE_ID,
    )
    mock_get_jobs.assert_called_with(SERVICE_ONE_ID)
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    banner = page.select("a.banner-dashboard")[1]
    assert normalize_spaces(banner.text) == "0 text messages received"
    assert banner["href"] == url_for("main.inbox", service_id=SERVICE_ONE_ID)


@pytest.mark.parametrize(
    ("index", "expected_row"),
    enumerate(
        [
            "(202) 867-5300 message-1 1 hour ago",
            "(202) 867-5300 message-2 1 hour ago",
            "(202) 867-5300 message-3 1 hour ago",
            "(202) 867-5302 message-4 3 hours ago",
            "+33(0)1 12345678 message-5 5 hours ago",
            "(202) 555-0104 message-6 7 hours ago",
            "(202) 555-0104 message-7 9 hours ago",
        ]
    ),
)
def test_inbox_showing_inbound_messages(
    client_request,
    service_one,
    mock_get_service_templates_when_no_templates_exist,
    mock_get_service_statistics,
    mock_get_template_statistics,
    mock_get_annual_usage_for_service,
    mock_get_most_recent_inbound_sms,
    index,
    expected_row,
):
    service_one["permissions"] = ["inbound_sms"]

    page = client_request.get(
        "main.inbox",
        service_id=SERVICE_ONE_ID,
    )

    rows = page.select("tbody tr")
    assert len(rows) == 8
    assert normalize_spaces(rows[index].text) == expected_row
    assert page.select_one("a[download]")["href"] == url_for(
        "main.inbox_download",
        service_id=SERVICE_ONE_ID,
    )


def test_get_inbound_sms_shows_page_links(
    client_request,
    service_one,
    mock_get_service_templates_when_no_templates_exist,
    mock_get_service_statistics,
    mock_get_template_statistics,
    mock_get_annual_usage_for_service,
    mock_get_most_recent_inbound_sms,
    mock_get_inbound_number_for_service,
):
    service_one["permissions"] = ["inbound_sms"]

    page = client_request.get(
        "main.inbox",
        service_id=SERVICE_ONE_ID,
        page=2,
    )

    assert "Next page" in page.find("li", {"class": "next-page"}).text
    assert "Previous page" in page.find("li", {"class": "previous-page"}).text


def test_empty_inbox(
    client_request,
    service_one,
    mock_get_service_templates_when_no_templates_exist,
    mock_get_service_statistics,
    mock_get_template_statistics,
    mock_get_annual_usage_for_service,
    mock_get_most_recent_inbound_sms_with_no_messages,
    mock_get_inbound_number_for_service,
):
    service_one["permissions"] = ["inbound_sms"]

    page = client_request.get(
        "main.inbox",
        service_id=SERVICE_ONE_ID,
    )

    assert normalize_spaces(page.select("tbody tr")) == (
        "When users text your service’s phone number (2028675301) you’ll see the messages here"
    )
    assert not page.select("a[download]")
    assert not page.select("li.next-page")
    assert not page.select("li.previous-page")


@pytest.mark.parametrize(
    "endpoint",
    [
        "main.inbox",
        "main.inbox_updates",
    ],
)
def test_inbox_not_accessible_to_service_without_permissions(
    client_request,
    service_one,
    endpoint,
):
    service_one["permissions"] = []
    client_request.get(
        endpoint,
        service_id=SERVICE_ONE_ID,
        _expected_status=403,
    )


def test_anyone_can_see_inbox(
    client_request,
    api_user_active,
    service_one,
    mocker,
    mock_get_most_recent_inbound_sms_with_no_messages,
    mock_get_inbound_number_for_service,
):
    service_one["permissions"] = ["inbound_sms"]

    validate_route_permission_with_client(
        mocker,
        client_request,
        "GET",
        200,
        url_for("main.inbox", service_id=service_one["id"]),
        ["view_activity"],
        api_user_active,
        service_one,
    )


def test_view_inbox_updates(
    client_request,
    service_one,
    mocker,
    mock_get_most_recent_inbound_sms_with_no_messages,
):
    service_one["permissions"] += ["inbound_sms"]

    mock_get_partials = mocker.patch(
        "app.main.views.dashboard.get_inbox_partials",
        return_value={"messages": "foo"},
    )

    response = client_request.get_response(
        "main.inbox_updates",
        service_id=SERVICE_ONE_ID,
    )

    assert json.loads(response.get_data(as_text=True)) == {"messages": "foo"}

    mock_get_partials.assert_called_once_with(SERVICE_ONE_ID)


@freeze_time("2016-07-01 16:00")
def test_download_inbox(
    client_request,
    mock_get_inbound_sms,
):
    response = client_request.get_response(
        "main.inbox_download",
        service_id=SERVICE_ONE_ID,
    )
    assert response.headers["Content-Type"] == ("text/csv; " "charset=utf-8")
    assert response.headers["Content-Disposition"] == (
        "inline; " 'filename="Received text messages 07-01-2016.csv"'
    )
    assert response.get_data(as_text=True) == (
        "Phone number,Message,Received\r\n"
        "(202) 867-5300,message-1,07-01-2016 11:00 US/Eastern\r\n"
        "(202) 867-5300,message-2,07-01-2016 10:59 US/Eastern\r\n"
        "(202) 867-5300,message-3,07-01-2016 10:59 US/Eastern\r\n"
        "(202) 867-5302,message-4,07-01-2016 08:59 US/Eastern\r\n"
        "+33(0)1 12345678,message-5,07-01-2016 06:59 US/Eastern\r\n"
        "(202) 555-0104,message-6,07-01-2016 04:59 US/Eastern\r\n"
        "(202) 555-0104,message-7,07-01-2016 02:59 US/Eastern\r\n"
        "+68212345,message-8,07-01-2016 02:59 US/Eastern\r\n"
    )


@freeze_time("2016-07-01 13:00")
@pytest.mark.parametrize(
    ("message_content", "expected_cell"),
    [
        ("=2+5", "2+5"),
        ("==2+5", "2+5"),
        ("-2+5", "2+5"),
        ("+2+5", "2+5"),
        ("@2+5", "2+5"),
        ("looks safe,=2+5", '"looks safe,=2+5"'),
    ],
)
def test_download_inbox_strips_formulae(
    mocker,
    client_request,
    fake_uuid,
    message_content,
    expected_cell,
):
    mocker.patch(
        "app.service_api_client.get_inbound_sms",
        return_value={
            "has_next": False,
            "data": [
                {
                    "user_number": "elevenchars",
                    "notify_number": "foo",
                    "content": message_content,
                    "created_at": datetime.utcnow().isoformat(),
                    "id": fake_uuid,
                }
            ],
        },
    )
    response = client_request.get_response(
        "main.inbox_download",
        service_id=SERVICE_ONE_ID,
    )
    assert expected_cell in response.get_data(as_text=True).split("\r\n")[1]


def test_should_show_recent_templates_on_dashboard(
    client_request,
    mocker,
    mock_get_service_templates,
    mock_has_no_jobs,
    mock_get_service_statistics,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    mock_template_stats = mocker.patch(
        "app.template_statistics_client.get_template_statistics_for_service",
        return_value=copy.deepcopy(stub_template_stats),
    )
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )
    page = client_request.get(
        "main.service_dashboard",
        service_id=SERVICE_ONE_ID,
    )

    mock_template_stats.assert_called_once_with(SERVICE_ONE_ID, limit_days=7)

    headers = [
        header.text.strip() for header in page.find_all("h2") + page.find_all("h1")
    ]
    assert "Messages sent" in headers

    table_rows = page.find_all("tbody")[0].find_all("tr")

    assert len(table_rows) == 2

    assert "two" in table_rows[0].find_all("th")[0].text
    assert "Email template" in table_rows[0].find_all("th")[0].text
    assert "200" in table_rows[0].find_all("td")[0].text

    assert "one" in table_rows[1].find_all("th")[0].text
    assert "Text message template" in table_rows[1].find_all("th")[0].text
    assert "100" in table_rows[1].find_all("td")[0].text


@pytest.mark.parametrize(
    "stats",
    [
        pytest.param(
            [stub_template_stats[0]],
        ),
        pytest.param(
            [stub_template_stats[0], stub_template_stats[1]],
            marks=pytest.mark.xfail(raises=AssertionError),
        ),
    ],
)
def test_should_not_show_recent_templates_on_dashboard_if_only_one_template_used(
    client_request,
    mocker,
    mock_get_service_templates,
    mock_has_no_jobs,
    mock_get_service_statistics,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
    stats,
):
    mock_template_stats = mocker.patch(
        "app.template_statistics_client.get_template_statistics_for_service",
        return_value=stats,
    )
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )
    page = client_request.get("main.service_dashboard", service_id=SERVICE_ONE_ID)
    main = page.select_one("main").text

    mock_template_stats.assert_called_once_with(SERVICE_ONE_ID, limit_days=7)

    assert stats[0]["template_name"] == "one"
    assert stats[0]["template_name"] not in main

    # count appears as total, but not per template
    expected_count = stats[0]["count"]
    assert expected_count == 50
    assert normalize_spaces(page.select_one("#total-sms .big-number-smaller").text) == (
        "{} text messages sent in the last seven days".format(expected_count)
    )


@freeze_time("2016-07-01 12:00")  # 4 months into 2016 financial year
@pytest.mark.parametrize(
    "extra_args",
    [
        {},
        {"year": "2016"},
    ],
)
def test_should_show_redirect_from_template_history(
    client_request,
    extra_args,
):
    client_request.get(
        "main.template_history",
        service_id=SERVICE_ONE_ID,
        _expected_status=301,
        **extra_args,
    )


@freeze_time("2017-01-01 12:00")
@pytest.mark.parametrize(
    "extra_args",
    [
        {},
        {"year": "2017"},
    ],
)
def test_should_show_monthly_breakdown_of_template_usage(
    client_request,
    mock_get_monthly_template_usage,
    extra_args,
):
    page = client_request.get(
        "main.template_usage", service_id=SERVICE_ONE_ID, **extra_args
    )

    mock_get_monthly_template_usage.assert_called_once_with(SERVICE_ONE_ID, 2017)

    table_rows = page.select("tbody tr")

    assert " ".join(table_rows[0].text.split()) == (
        "My first template " "Text message template " "2"
    )

    assert len(table_rows) == len(["January"])
    # October is the only month with data, thus it's not in the list.
    assert len(page.select(".table-no-data")) == len(
        [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "November",
            "December",
        ]
    )


def test_anyone_can_see_monthly_breakdown(
    client_request,
    api_user_active,
    service_one,
    mocker,
    mock_get_monthly_notification_stats,
):
    validate_route_permission_with_client(
        mocker,
        client_request,
        "GET",
        200,
        url_for("main.monthly", service_id=service_one["id"]),
        ["view_activity"],
        api_user_active,
        service_one,
    )


@pytest.mark.parametrize(
    "endpoint",
    [
        "main.monthly",
        "main.template_usage",
    ],
)
@freeze_time("2015-01-01 15:15:15.000000")
def test_stats_pages_show_last_3_years(
    client_request,
    endpoint,
    mock_get_monthly_notification_stats,
    mock_get_monthly_template_usage,
):
    page = client_request.get(
        endpoint,
        service_id=SERVICE_ONE_ID,
    )

    assert normalize_spaces(page.select_one(".pill").text) == (
        "2015 to 2016 fiscal year "
        "2014 to 2015 fiscal year "
        "2013 to 2014 fiscal year"
    )


def test_monthly_has_equal_length_tables(
    client_request,
    service_one,
    mock_get_monthly_notification_stats,
):
    page = client_request.get("main.monthly", service_id=service_one["id"])

    assert page.select_one(".table-field-headings th").get("width") == "33%"


@freeze_time("2016-01-01 11:09:00.061258")
def test_should_show_upcoming_jobs_on_dashboard(
    mocker,
    client_request,
    mock_get_service_templates,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_get_jobs,
    mock_get_scheduled_job_stats,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )
    page = client_request.get(
        "main.service_dashboard",
        service_id=SERVICE_ONE_ID,
    )

    mock_get_jobs.assert_called_with(SERVICE_ONE_ID)
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    mock_get_scheduled_job_stats.assert_called_once_with(SERVICE_ONE_ID)

    assert normalize_spaces(page.select_one("main h2").text) == ("In the next few days")

    assert normalize_spaces(page.select_one("a.banner-dashboard").text) == (
        "2 files waiting to send " "- sending starts today at 06:09 US/Eastern"
    )

    assert page.select_one("a.banner-dashboard")["href"] == url_for(
        "main.uploads", service_id=SERVICE_ONE_ID
    )


def test_should_not_show_upcoming_jobs_on_dashboard_if_count_is_0(
    mocker,
    client_request,
    mock_get_service_templates,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_has_jobs,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    mocker.patch(
        "app.job_api_client.get_scheduled_job_stats",
        return_value={
            "count": 0,
            "soonest_scheduled_for": None,
        },
    )
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )
    page = client_request.get(
        "main.service_dashboard",
        service_id=SERVICE_ONE_ID,
    )
    mock_has_jobs.assert_called_once_with(SERVICE_ONE_ID)
    assert "In the next few days" not in page.select_one("main").text
    assert "files waiting to send " not in page.select_one("main").text


def test_should_not_show_upcoming_jobs_on_dashboard_if_service_has_no_jobs(
    mocker,
    client_request,
    mock_get_service_templates,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_has_no_jobs,
    mock_get_scheduled_job_stats,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )
    page = client_request.get(
        "main.service_dashboard",
        service_id=SERVICE_ONE_ID,
    )
    mock_has_no_jobs.assert_called_once_with(SERVICE_ONE_ID)
    assert mock_get_scheduled_job_stats.called is False
    assert "In the next few days" not in page.select_one("main").text
    assert "files waiting to send " not in page.select_one("main").text


@pytest.mark.parametrize(
    "permissions",
    [
        ("email", "sms"),
    ],
)
@pytest.mark.parametrize(
    "totals",
    [
        (
            {
                "email": {"requested": 0, "delivered": 0, "failed": 0},
                "sms": {"requested": 99999, "delivered": 0, "failed": 0},
            },
        ),
        (
            {
                "email": {"requested": 0, "delivered": 0, "failed": 0},
                "sms": {"requested": 0, "delivered": 0, "failed": 0},
            },
        ),
    ],
)
def test_correct_font_size_for_big_numbers(
    client_request,
    mocker,
    mock_get_service_templates,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_has_no_jobs,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    service_one,
    permissions,
    totals,
):
    service_one["permissions"] = permissions

    mocker.patch("app.main.views.dashboard.get_dashboard_totals", return_value=totals)
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )
    page = client_request.get(
        "main.service_dashboard",
        service_id=service_one["id"],
    )

    assert (
        (len(page.select_one("[data-key=totals]").select(".grid-col-12")))
        == (
            #     len(page.select_one('[data-key=usage]').select('.grid-col-6'))
            # ) == (
            len(page.select(".big-number-with-status .big-number-smaller"))
        )
        == 1
    )


def test_should_not_show_jobs_on_dashboard_for_users_with_uploads_page(
    mocker,
    client_request,
    service_one,
    mock_get_service_templates,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_get_jobs,
    mock_get_scheduled_job_stats,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )
    page = client_request.get(
        "main.service_dashboard",
        service_id=SERVICE_ONE_ID,
    )
    mock_get_jobs.assert_called_with(SERVICE_ONE_ID)
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    for filename in {
        "export 1/1/2016.xls",
        "all email addresses.xlsx",
        "applicants.ods",
        "thisisatest.csv",
    }:
        assert filename not in page.select_one("main").text


@freeze_time("2012-03-31 12:12:12")
def test_usage_page(
    client_request,
    mock_get_annual_usage_for_service,
    mock_get_monthly_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_monthly_notification_stats,
):
    page = client_request.get(
        "main.usage",
        service_id=SERVICE_ONE_ID,
    )

    mock_get_monthly_usage_for_service.assert_called_once_with(SERVICE_ONE_ID, 2012)
    mock_get_annual_usage_for_service.assert_called_once_with(SERVICE_ONE_ID, 2012)
    mock_get_free_sms_fragment_limit.assert_called_with(SERVICE_ONE_ID)

    nav = page.find("ul", {"class": "pill"})
    unselected_nav_links = nav.select("a:not(.pill-item--selected)")
    assert (
        normalize_spaces(nav.find("a", {"aria-current": "page"}).text)
        == "2012 to 2013 fiscal year"
    )
    assert normalize_spaces(unselected_nav_links[0].text) == "2011 to 2012 fiscal year"
    assert normalize_spaces(unselected_nav_links[1].text) == "2010 to 2011 fiscal year"

    annual_usage = page.find_all("div", {"class": "keyline-block"})

    # annual stats are shown in two rows, each with three column; email is col 1
    # email_column = normalize_spaces(annual_usage[0].text + annual_usage[2].text)
    # assert 'Emails' in email_column
    # assert '1,000 sent' in email_column

    sms_column = normalize_spaces(annual_usage[0].text)
    assert (
        "You have sent 251,800 text message parts of your 250,000 free message parts allowance."
        " You have 0 message parts remaining." in sms_column
    )
    assert "$29.85 spent" not in sms_column
    assert "1,500 at 1.65 pence" not in sms_column
    assert "300 at 1.70 pence" not in sms_column


@freeze_time("2012-03-31 12:12:12")
def test_usage_page_no_sms_spend(
    mocker,
    client_request,
    mock_get_monthly_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_monthly_notification_stats,
):
    mocker.patch(
        "app.billing_api_client.get_annual_usage_for_service",
        return_value=[
            {
                "notification_type": "sms",
                "chargeable_units": 1000,
                "charged_units": 0,
                "rate": 0.0165,
                "cost": 0,
            }
        ],
    )

    page = client_request.get(
        "main.usage",
        service_id=SERVICE_ONE_ID,
    )

    annual_usage = page.find_all("div", {"class": "keyline-block"})
    sms_column = normalize_spaces(annual_usage[0].text)
    assert (
        "You have sent 1,000 text message parts of your 250,000 free message parts allowance."
        " You have 249,000 message parts remaining." in sms_column
    )
    assert "$0.00 spent" not in sms_column
    assert "pence per message" not in sms_column


@freeze_time("2012-03-31 12:12:12")
def test_usage_page_monthly_breakdown(
    client_request,
    service_one,
    mock_get_annual_usage_for_service,
    mock_get_monthly_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_monthly_notification_stats,
):
    page = client_request.get("main.usage", service_id=SERVICE_ONE_ID)
    monthly_breakdown = normalize_spaces(page.find("table").text)

    assert "January" in monthly_breakdown
    assert "October" in monthly_breakdown
    assert "February" in monthly_breakdown
    assert "March" in monthly_breakdown


@pytest.mark.parametrize(
    ("now", "expected_number_of_months"),
    [
        (freeze_time("2017-03-31 11:09:00.061258"), 12),
        (freeze_time("2017-01-01 11:09:00.061258"), 12),
    ],
)
def test_usage_page_monthly_breakdown_shows_months_so_far(
    client_request,
    service_one,
    mock_get_annual_usage_for_service,
    mock_get_monthly_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_monthly_notification_stats,
    now,
    expected_number_of_months,
):
    with now:
        page = client_request.get("main.usage", service_id=SERVICE_ONE_ID)
        rows = page.find("table").find_all("tr", class_="table-row")
        assert len(rows) == expected_number_of_months


def test_usage_page_with_0_free_allowance(
    mocker,
    client_request,
    mock_get_annual_usage_for_service,
    mock_get_monthly_usage_for_service,
    mock_get_monthly_notification_stats,
):
    mocker.patch(
        "app.billing_api_client.get_free_sms_fragment_limit_for_year",
        return_value=0,
    )
    page = client_request.get(
        "main.usage",
        service_id=SERVICE_ONE_ID,
        year=2020,
    )

    annual_usage = page.select("main .grid-col-12 .keyline-block")
    sms_column = normalize_spaces(annual_usage[0].text)

    assert (
        "You have sent 251,800 text message parts of your 0 free message parts allowance. You have"
        in sms_column
    )
    assert "free allowance remaining" not in sms_column


def test_usage_page_with_year_argument(
    client_request,
    mock_get_annual_usage_for_service,
    mock_get_monthly_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_monthly_notification_stats,
):
    client_request.get(
        "main.usage",
        service_id=SERVICE_ONE_ID,
        year=2000,
    )
    mock_get_monthly_usage_for_service.assert_called_once_with(SERVICE_ONE_ID, 2000)
    mock_get_annual_usage_for_service.assert_called_once_with(SERVICE_ONE_ID, 2000)
    mock_get_free_sms_fragment_limit.assert_called_with(SERVICE_ONE_ID)
    mock_get_monthly_notification_stats.assert_called_with(SERVICE_ONE_ID, 2000)


def test_usage_page_for_invalid_year(
    client_request,
):
    client_request.get(
        "main.usage",
        service_id=SERVICE_ONE_ID,
        year="abcd",
        _expected_status=404,
    )


@freeze_time("2012-03-31 12:12:12")
def test_future_usage_page(
    client_request,
    mock_get_annual_usage_for_service_in_future,
    mock_get_monthly_usage_for_service_in_future,
    mock_get_free_sms_fragment_limit,
    mock_get_monthly_notification_stats,
):
    client_request.get(
        "main.usage",
        service_id=SERVICE_ONE_ID,
        year=2014,
    )

    mock_get_monthly_usage_for_service_in_future.assert_called_once_with(
        SERVICE_ONE_ID, 2014
    )
    mock_get_annual_usage_for_service_in_future.assert_called_once_with(
        SERVICE_ONE_ID, 2014
    )
    mock_get_free_sms_fragment_limit.assert_called_with(SERVICE_ONE_ID)
    mock_get_monthly_notification_stats.assert_called_with(SERVICE_ONE_ID, 2014)


def _test_dashboard_menu(client_request, mocker, usr, service, permissions):
    usr["permissions"][str(service["id"])] = permissions
    usr["services"] = [service["id"]]
    mocker.patch("app.user_api_client.check_verify_code", return_value=(True, ""))
    mocker.patch(
        "app.service_api_client.get_services", return_value={"data": [service]}
    )
    mocker.patch("app.user_api_client.get_user", return_value=usr)
    mocker.patch("app.user_api_client.get_user_by_email", return_value=usr)
    mocker.patch("app.service_api_client.get_service", return_value={"data": service})
    client_request.login(usr)
    return client_request.get("main.service_dashboard", service_id=service["id"])


def _test_settings_menu(client_request, mocker, usr, service, permissions):
    usr["permissions"][str(service["id"])] = permissions
    usr["services"] = [service["id"]]
    mocker.patch("app.user_api_client.check_verify_code", return_value=(True, ""))
    mocker.patch(
        "app.service_api_client.get_services", return_value={"data": [service]}
    )
    mocker.patch("app.user_api_client.get_user", return_value=usr)
    mocker.patch("app.user_api_client.get_user_by_email", return_value=usr)
    mocker.patch("app.service_api_client.get_service", return_value={"data": service})
    client_request.login(usr)
    return client_request.get("main.service_dashboard", service_id=service["id"])


def test_menu_send_messages(
    client_request,
    mocker,
    notify_admin,
    api_user_active,
    service_one,
    mock_get_service_templates,
    mock_has_no_jobs,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_get_annual_usage_for_service,
    mock_get_inbound_sms_summary,
    mock_get_free_sms_fragment_limit,
):
    service_one["permissions"] = ["email", "sms"]

    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )
    page = _test_dashboard_menu(
        client_request,
        mocker,
        api_user_active,
        service_one,
        ["view_activity", "send_texts", "send_emails"],
    )
    page = str(page)
    assert (
        url_for(
            "main.choose_template",
            service_id=service_one["id"],
        )
        in page
    )
    assert url_for("main.manage_users", service_id=service_one["id"]) not in page
    assert url_for("main.service_settings", service_id=service_one["id"]) in page


def test_menu_manage_service(
    client_request,
    mocker,
    api_user_active,
    service_one,
    mock_get_service_templates,
    mock_has_no_jobs,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_get_annual_usage_for_service,
    mock_get_inbound_sms_summary,
    mock_get_free_sms_fragment_limit,
):
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )
    page = _test_dashboard_menu(
        client_request,
        mocker,
        api_user_active,
        service_one,
        ["view_activity", "manage_templates", "manage_users", "manage_settings"],
    )
    page = str(page)
    assert (
        url_for(
            "main.choose_template",
            service_id=service_one["id"],
        )
        in page
    )
    assert url_for(".service_dashboard", service_id=service_one["id"]) in page
    assert url_for(".choose_template", service_id=service_one["id"]) in page


def test_menu_main_settings(
    client_request,
    mocker,
    api_user_active,
    service_one,
    mock_get_service_templates,
    mock_has_no_jobs,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_get_annual_usage_for_service,
    mock_get_inbound_sms_summary,
    mock_get_free_sms_fragment_limit,
):
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )
    page = _test_settings_menu(
        client_request,
        mocker,
        api_user_active,
        service_one,
        ["view_activity", "user_profile", "manage_users", "manage_settings"],
    )
    page = str(page)
    assert (
        url_for(
            "main.service_settings",
            service_id=service_one["id"],
        )
        in page
    )
    assert url_for("main.service_settings", service_id=service_one["id"]) in page


def test_menu_manage_api_keys(
    client_request,
    mocker,
    api_user_active,
    service_one,
    mock_get_service_templates,
    mock_has_no_jobs,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_get_annual_usage_for_service,
    mock_get_inbound_sms_summary,
    mock_get_free_sms_fragment_limit,
):
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )
    page = _test_dashboard_menu(
        client_request,
        mocker,
        api_user_active,
        service_one,
        ["view_activity", "manage_api_keys"],
    )

    page = str(page)

    assert (
        url_for(
            "main.choose_template",
            service_id=service_one["id"],
        )
        in page
    )
    # assert url_for("main.manage_users", service_id=service_one["id"]) not in page
    # assert url_for("main.service_settings", service_id=service_one["id"]) not in page
    assert url_for("main.api_integration", service_id=service_one["id"]) in page


def test_menu_all_services_for_platform_admin_user(
    client_request,
    mocker,
    platform_admin_user,
    service_one,
    mock_get_service_templates,
    mock_has_no_jobs,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_get_annual_usage_for_service,
    mock_get_inbound_sms_summary,
    mock_get_free_sms_fragment_limit,
):
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )
    page = _test_dashboard_menu(
        client_request, mocker, platform_admin_user, service_one, []
    )
    page = str(page)
    assert url_for("main.choose_template", service_id=service_one["id"]) in page
    # assert url_for("main.manage_users", service_id=service_one["id"]) in page
    # assert url_for("main.service_settings", service_id=service_one["id"]) in page
    # assert url_for('main.view_notifications', service_id=service_one['id'], message_type='email') in page
    assert (
        url_for(
            "main.view_notifications", service_id=service_one["id"], message_type="sms"
        )
        in page
    )
    # assert url_for('main.api_keys', service_id=service_one['id']) not in page


def test_route_for_service_permissions(
    mocker,
    notify_admin,
    api_user_active,
    service_one,
    mock_get_service,
    mock_get_user,
    mock_get_service_templates,
    mock_has_no_jobs,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_get_monthly_usage_for_service,
    mock_get_annual_usage_for_service,
    mock_create_or_update_free_sms_fragment_limit,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    with notify_admin.test_request_context():

        def _get(mocker):
            return {"count": 0}

        mocker.patch(
            "app.service_api_client.get_global_notification_count", side_effect=_get
        )
        mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
        mocker.patch(
            "app.notification_api_client.get_notifications_for_service",
            return_value=FAKE_ONE_OFF_NOTIFICATION,
        )
        validate_route_permission(
            mocker,
            notify_admin,
            "GET",
            200,
            url_for("main.service_dashboard", service_id=service_one["id"]),
            ["view_activity"],
            api_user_active,
            service_one,
        )


def test_aggregate_template_stats():
    expected = aggregate_template_usage(copy.deepcopy(stub_template_stats))
    assert len(expected) == 2
    assert expected[0]["template_name"] == "two"
    assert expected[0]["count"] == 200
    assert expected[0]["template_id"] == "id-2"
    assert expected[0]["template_type"] == "email"
    assert expected[1]["template_name"] == "one"
    assert expected[1]["count"] == 100
    assert expected[1]["template_id"] == "id-1"
    assert expected[1]["template_type"] == "sms"


def test_aggregate_notifications_stats():
    expected = aggregate_notifications_stats(copy.deepcopy(stub_template_stats))
    assert expected == {
        "sms": {"requested": 100, "delivered": 50, "failed": 0},
        "email": {"requested": 200, "delivered": 0, "failed": 100},
    }


def test_service_dashboard_updates_gets_dashboard_totals(
    mocker,
    client_request,
    mock_get_service_templates,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_has_no_jobs,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    mocker.patch(
        "app.main.views.dashboard.get_dashboard_totals",
        return_value={
            "email": {"requested": 123, "delivered": 0, "failed": 0},
            "sms": {"requested": 456, "delivered": 0, "failed": 0},
        },
    )
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )

    page = client_request.get(
        "main.service_dashboard",
        service_id=SERVICE_ONE_ID,
    )

    numbers = [
        number.text.strip()
        for number in page.find_all("span", class_="big-number-number")
    ]
    # assert '123' in numbers  # email is disabled
    assert "456" in numbers


def test_get_dashboard_totals_adds_percentages():
    stats = {
        "sms": {"requested": 3, "delivered": 0, "failed": 2},
        "email": {"requested": 0, "delivered": 0, "failed": 0},
    }
    assert get_dashboard_totals(stats)["sms"]["failed_percentage"] == "66.7"
    assert get_dashboard_totals(stats)["email"]["failed_percentage"] == "0"


@pytest.mark.parametrize(("failures", "expected"), [(2, False), (3, False), (4, True)])
def test_get_dashboard_totals_adds_warning(failures, expected):
    stats = {"sms": {"requested": 100, "delivered": 0, "failed": failures}}
    assert get_dashboard_totals(stats)["sms"]["show_warning"] == expected


def test_format_monthly_stats_empty_case():
    assert format_monthly_stats_to_list({}) == []


def test_format_monthly_stats_labels_month():
    resp = format_monthly_stats_to_list({"2016-07": {}})
    assert resp[0]["name"] == "July"


def test_format_monthly_stats_has_stats_with_failure_rate():
    resp = format_monthly_stats_to_list({"2016-07": {"sms": _stats(3, 1, 2)}})
    assert resp[0]["sms_counts"] == {
        "failed": 2,
        "failed_percentage": "66.7",
        "requested": 3,
        "show_warning": True,
    }


def test_format_monthly_stats_works_for_email():
    resp = format_monthly_stats_to_list(
        {
            "2016-07": {
                "sms": {},
                "email": {},
            }
        }
    )
    assert isinstance(resp[0]["sms_counts"], dict)
    assert isinstance(resp[0]["email_counts"], dict)


def _stats(requested, delivered, failed):
    return {"requested": requested, "delivered": delivered, "failed": failed}


@pytest.mark.parametrize(
    ("dict_in", "expected_failed", "expected_requested"),
    [
        ({}, 0, 0),
        (
            {"temporary-failure": 1, "permanent-failure": 1, "technical-failure": 1},
            3,
            3,
        ),
        (
            {"created": 1, "pending": 1, "sending": 1, "delivered": 1},
            0,
            4,
        ),
    ],
)
def test_aggregate_status_types(dict_in, expected_failed, expected_requested):
    sms_counts = aggregate_status_types({"sms": dict_in})["sms_counts"]
    assert sms_counts["failed"] == expected_failed
    assert sms_counts["requested"] == expected_requested


def test_get_tuples_of_financial_years():
    assert list(
        get_tuples_of_financial_years(
            lambda year: "http://example.com?year={}".format(year),
            start=2040,
            end=2041,
        )
    ) == [
        ("fiscal year", 2041, "http://example.com?year=2041", "2041 to 2042"),
        ("fiscal year", 2040, "http://example.com?year=2040", "2040 to 2041"),
    ]


def test_get_tuples_of_financial_years_defaults_to_2015():
    assert (
        2015
        in list(
            get_tuples_of_financial_years(
                lambda year: "http://example.com?year={}".format(year),
                end=2040,
            )
        )[-1]
    )


def test_org_breadcrumbs_do_not_show_if_service_has_no_org(
    mocker,
    client_request,
    mock_get_template_statistics,
    mock_get_service_templates_when_no_templates_exist,
    mock_has_no_jobs,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
):
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )
    page = client_request.get("main.service_dashboard", service_id=SERVICE_ONE_ID)

    assert not page.select(".navigation-organization-link")


def test_org_breadcrumbs_do_not_show_if_user_is_not_an_org_member(
    mocker,
    mock_get_service_templates_when_no_templates_exist,
    mock_has_no_jobs,
    active_caseworking_user,
    client_request,
    mock_get_template_folders,
    mock_get_api_keys,
):
    # active_caseworking_user is not an org member

    service_one_json = service_json(
        SERVICE_ONE_ID,
        users=[active_caseworking_user["id"]],
        restricted=False,
        organization_id=ORGANISATION_ID,
    )
    mocker.patch(
        "app.service_api_client.get_service", return_value={"data": service_one_json}
    )

    client_request.login(active_caseworking_user, service=service_one_json)
    page = client_request.get(
        "main.service_dashboard", service_id=SERVICE_ONE_ID, _follow_redirects=True
    )

    assert not page.select(".navigation-organization-link")


def test_org_breadcrumbs_show_if_user_is_a_member_of_the_services_org(
    mocker,
    mock_get_template_statistics,
    mock_get_service_templates_when_no_templates_exist,
    mock_has_no_jobs,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    active_user_with_permissions,
    client_request,
):
    # active_user_with_permissions (used by the client_request) is an org member

    service_one_json = service_json(
        SERVICE_ONE_ID,
        users=[active_user_with_permissions["id"]],
        restricted=False,
        organization_id=ORGANISATION_ID,
    )

    mocker.patch(
        "app.service_api_client.get_service", return_value={"data": service_one_json}
    )
    mocker.patch(
        "app.organizations_client.get_organization",
        return_value=organization_json(
            id_=ORGANISATION_ID,
        ),
    )
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )

    page = client_request.get("main.service_dashboard", service_id=SERVICE_ONE_ID)
    assert page.select_one(".navigation-organization-link")["href"] == url_for(
        "main.organization_dashboard",
        org_id=ORGANISATION_ID,
    )


def test_org_breadcrumbs_do_not_show_if_user_is_a_member_of_the_services_org_but_service_is_in_trial_mode(
    mocker,
    mock_get_template_statistics,
    mock_get_service_templates_when_no_templates_exist,
    mock_has_no_jobs,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    active_user_with_permissions,
    client_request,
):
    # active_user_with_permissions (used by the client_request) is an org member

    service_one_json = service_json(
        SERVICE_ONE_ID,
        users=[active_user_with_permissions["id"]],
        organization_id=ORGANISATION_ID,
    )

    mocker.patch(
        "app.service_api_client.get_service", return_value={"data": service_one_json}
    )
    mocker.patch("app.models.service.Organization")

    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)

    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )

    page = client_request.get("main.service_dashboard", service_id=SERVICE_ONE_ID)

    assert not page.select(".navigation-breadcrumb")


def test_org_breadcrumbs_show_if_user_is_platform_admin(
    mocker,
    mock_get_template_statistics,
    mock_get_service_templates_when_no_templates_exist,
    mock_has_no_jobs,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    platform_admin_user,
    client_request,
):
    service_one_json = service_json(
        SERVICE_ONE_ID,
        users=[platform_admin_user["id"]],
        organization_id=ORGANISATION_ID,
    )

    mocker.patch(
        "app.service_api_client.get_service", return_value={"data": service_one_json}
    )
    mocker.patch(
        "app.organizations_client.get_organization",
        return_value=organization_json(
            id_=ORGANISATION_ID,
        ),
    )

    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)

    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )

    client_request.login(platform_admin_user, service_one_json)
    page = client_request.get("main.service_dashboard", service_id=SERVICE_ONE_ID)

    assert page.select_one(".navigation-organization-link")["href"] == url_for(
        "main.organization_dashboard",
        org_id=ORGANISATION_ID,
    )


def test_breadcrumb_shows_if_service_is_suspended(
    mocker,
    mock_get_template_statistics,
    mock_get_service_templates_when_no_templates_exist,
    mock_has_no_jobs,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    active_user_with_permissions,
    client_request,
):
    service_one_json = service_json(
        SERVICE_ONE_ID,
        active=False,
        users=[active_user_with_permissions["id"]],
    )

    mocker.patch(
        "app.service_api_client.get_service", return_value={"data": service_one_json}
    )

    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)

    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )
    page = client_request.get("main.service_dashboard", service_id=SERVICE_ONE_ID)

    assert "Suspended" in page.select_one(".navigation-service-name").text


@pytest.mark.parametrize(
    "permissions",
    [
        ("email", "sms"),
    ],
)
def test_service_dashboard_shows_usage(
    mocker,
    client_request,
    service_one,
    mock_get_service_templates,
    mock_get_template_statistics,
    mock_has_no_jobs,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    permissions,
):
    mocker.patch(
        "app.service_api_client.get_global_notification_count",
        return_value={
            "count": 500,
        },
    )
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )

    service_one["permissions"] = permissions
    page = client_request.get("main.service_dashboard", service_id=SERVICE_ONE_ID)

    usage_table = page.find("table", class_="usage-table")

    # Check if the "Usage" table doesn't exist
    assert usage_table is None


def test_service_dashboard_shows_free_allowance(
    mocker,
    client_request,
    service_one,
    mock_get_service_templates,
    mock_get_template_statistics,
    mock_has_no_jobs,
    mock_get_free_sms_fragment_limit,
):
    mocker.patch(
        "app.billing_api_client.get_annual_usage_for_service",
        return_value=[
            {
                "notification_type": "sms",
                "chargeable_units": 1000,
                "charged_units": 0,
                "rate": 0.0165,
                "cost": 0,
            }
        ],
    )
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)

    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )


def test_service_dashboard_shows_batched_jobs(
    mocker,
    client_request,
    service_one,
    mock_get_service_templates,
    mock_get_template_statistics,
    mock_has_no_jobs,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
):
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )

    page = client_request.get("main.service_dashboard", service_id=SERVICE_ONE_ID)

    job_table_body = page.find("table", class_="job-table")

    rows = job_table_body.find_all("tbody")[0].find_all("tr")

    # # Check if the "Job" table exists
    assert job_table_body is not None

    assert len(rows) == 1


@pytest.fixture()
def app_with_socketio():
    app = Flask("app")
    create_app(app)
    return app, socketio


@pytest.mark.parametrize(
    ("service_id", "date_range", "expected_call_args"),
    [
        (
            SERVICE_ONE_ID,
            {"start_date": "2024-01-01", "days": 7},
            {"service_id": SERVICE_ONE_ID, "start_date": "2024-01-01", "days": 7}
        ),
        (
            SERVICE_TWO_ID,
            {"start_date": "2023-06-01", "days": 7},
            {"service_id": SERVICE_TWO_ID, "start_date": "2023-06-01", "days": 7}
        ),
    ]
)
def test_fetch_daily_stats(
    app_with_socketio, mocker,
    service_id,
    date_range,
    expected_call_args
):
    app, socketio = app_with_socketio

    mocker.patch(
        "app.main.views.dashboard.get_stats_date_range",
        return_value=date_range
    )

    mock_service_api = mocker.patch(
        "app.service_api_client.get_service_notification_statistics_by_day",
        return_value={
            date_range["start_date"]: {
                "email": {"delivered": 0, "failure": 0, "requested": 0},
                "sms": {"delivered": 0, "failure": 1, "requested": 1}
            },
        }
    )

    client = SocketIOTestClient(app, socketio)
    try:
        connected = client.is_connected()
        assert connected, "Client should be connected"

        client.emit('fetch_daily_stats', service_id)

        received = client.get_received()
        assert received, "Should receive a response message"
        assert received[0]['name'] == 'daily_stats_update'
        assert received[0]['args'][0] == {
            date_range["start_date"]: {
                "email": {"delivered": 0, "failure": 0, "requested": 0},
                "sms": {"delivered": 0, "failure": 1, "requested": 1}
            },
        }

        mock_service_api.assert_called_once_with(
            service_id,
            start_date=expected_call_args["start_date"],
            days=expected_call_args["days"]
        )
    finally:
        client.disconnect()
        disconnected = not client.is_connected()
        assert disconnected, "Client should be disconnected"
