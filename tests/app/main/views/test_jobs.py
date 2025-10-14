from datetime import datetime, timezone

import pytest
from flask import url_for
from freezegun import freeze_time
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from tests import job_json
from tests.conftest import (
    SERVICE_ONE_ID,
    create_active_caseworking_user,
    create_active_user_with_permissions,
    normalize_spaces,
)


def test_old_jobs_hub_redirects(
    client_request,
):
    client_request.get(
        "main.view_jobs",
        service_id=SERVICE_ONE_ID,
        _expected_status=302,
        _expected_redirect=url_for(
            "main.uploads",
            service_id=SERVICE_ONE_ID,
        ),
    )


@pytest.mark.parametrize(
    "user",
    [
        create_active_user_with_permissions(),
        create_active_caseworking_user(),
    ],
)
@pytest.mark.parametrize(
    ("status_argument", "expected_api_call"),
    [
        (
            "",
            [
                "created",
                "pending",
                "sending",
                "delivered",
                "sent",
                "failed",
                "temporary-failure",
                "permanent-failure",
                "technical-failure",
                "validation-failed",
            ],
        ),
        ("sending", ["sending", "created", "pending"]),
        ("delivered", ["delivered", "sent"]),
        (
            "failed",
            [
                "failed",
                "temporary-failure",
                "permanent-failure",
                "technical-failure",
                "validation-failed",
            ],
        ),
    ],
)
@freeze_time("2016-01-01 11:09:00.061258")
def test_should_show_page_for_one_job(
    client_request,
    mock_get_service_template,
    mock_get_job,
    mocker,
    mock_get_notifications,
    mock_get_service_data_retention,
    fake_uuid,
    status_argument,
    expected_api_call,
    user,
):
    page = client_request.get(
        "main.view_job",
        service_id=SERVICE_ONE_ID,
        job_id=fake_uuid,
        status=status_argument,
    )

    assert page.h1.text.strip() == "Message status"
    assert page.select_one('[data-key="counts"]') is not None
    assert page.select_one('[data-key="notifications"]') is not None


@freeze_time("2016-01-01 11:09:00.061258")
def test_should_show_page_for_one_job_with_flexible_data_retention(
    client_request,
    mock_get_service_template,
    mock_get_job,
    mock_get_service_data_retention,
    fake_uuid,
):
    mock_get_service_data_retention.side_effect = [
        [{"days_of_retention": 10, "notification_type": "sms"}]
    ]
    page = client_request.get(
        "main.view_job", service_id=SERVICE_ONE_ID, job_id=fake_uuid, status="delivered"
    )

    assert page.select_one('[data-key="counts"]') is not None


def test_get_jobs_should_tell_user_if_more_than_one_page(
    client_request,
    fake_uuid,
    service_one,
    mock_get_job,
    mock_get_service_template,
    mock_get_service_data_retention,
):
    page = client_request.get(
        "main.view_job",
        service_id=service_one["id"],
        job_id=fake_uuid,
        status="",
    )
    assert page.h1.text.strip() == "Message status"


def test_should_show_job_in_progress(
    client_request,
    service_one,
    mock_get_service_template,
    mock_get_job_in_progress,
    fake_uuid,
    mock_get_service_data_retention,
):
    page = client_request.get(
        "main.view_job",
        service_id=service_one["id"],
        job_id=fake_uuid,
    )
    assert page.h1.text.strip() == "Message status"
    assert page.select_one('[data-key="counts"]') is not None


def test_should_show_job_without_notifications(
    client_request,
    service_one,
    mock_get_service_template,
    mock_get_job_in_progress,
    fake_uuid,
    mock_get_service_data_retention,
):
    page = client_request.get(
        "main.view_job",
        service_id=service_one["id"],
        job_id=fake_uuid,
    )
    assert page.h1.text.strip() == "Message status"


def test_should_show_job_with_sending_limit_exceeded_status(
    client_request,
    service_one,
    mock_get_service_template,
    mock_get_job_with_sending_limits_exceeded,
    fake_uuid,
    mock_get_service_data_retention,
):
    page = client_request.get(
        "main.view_job",
        service_id=service_one["id"],
        job_id=fake_uuid,
    )

    assert page.h1.text.strip() == "Message status"


@freeze_time("2020-01-10 1:0:0")
@pytest.mark.parametrize(
    ("created_at", "processing_started", "expected_message"),
    [
        # Recently created, not yet started
        (datetime(2020, 1, 10, 0, 0, 0), None, ("No messages to show yet…")),
        # Just started
        (
            datetime(2020, 1, 10, 0, 0, 0),
            datetime(2020, 1, 10, 0, 0, 1),
            ("No messages to show yet…"),
        ),
        # Created a while ago, just started
        (
            datetime(2020, 1, 1, 0, 0, 0),
            datetime(2020, 1, 10, 0, 0, 1),
            ("No messages to show yet…"),
        ),
        # Created a while ago, started just within the last 24h
        # TODO -- fails locally, should pass, tech debt due to timezone changes, re-evaluate after UTC changes
        pytest.param(
            datetime(2020, 1, 1, 0, 0, 0),
            datetime(2020, 1, 9, 6, 0, 1),
            ("No messages to show yet…"),
        ),
        # Created a while ago, started exactly 24h ago
        # ---
        # It doesn't matter that 24h (1 day) and 7 days (the service's data
        # retention) don't match up. We're testing the case of no
        # notifications existing more than 1 day after the job started
        # processing. In this case we assume it's because the service's
        # data retention has kicked in.
        (
            datetime(2020, 1, 1, 0, 0, 0),
            datetime(2020, 1, 9, 1, 0, 0),
            (
                "These messages have been deleted because they were sent more than 7 days ago"
            ),
        ),
    ],
)
def test_should_show_old_job(
    client_request,
    mock_get_service_template,
    mocker,
    fake_uuid,
    created_at,
    processing_started,
    expected_message,
    active_user_with_permissions,
    mock_get_service_data_retention,
):
    mocker.patch(
        "app.job_api_client.get_job",
        return_value={
            "data": job_json(
                SERVICE_ONE_ID,
                active_user_with_permissions,
                created_at=created_at.replace(tzinfo=timezone.utc).isoformat(),
                processing_started=(
                    processing_started.replace(tzinfo=timezone.utc).isoformat()
                    if processing_started
                    else None
                ),
            ),
        },
    )
    page = client_request.get(
        "main.view_job",
        service_id=SERVICE_ONE_ID,
        job_id=fake_uuid,
    )
    assert page.h1.text.strip() == "Message status"


@freeze_time("2016-01-01T06:00:00.061258")
def test_should_show_scheduled_job(
    client_request,
    mock_get_service_template,
    mock_get_scheduled_job,
    fake_uuid,
    mock_get_service_data_retention,
):
    page = client_request.get(
        "main.view_job",
        service_id=SERVICE_ONE_ID,
        job_id=fake_uuid,
    )

    assert page.h1.text.strip() == "Message status"


def test_should_cancel_job(
    client_request,
    fake_uuid,
    mock_get_job,
    mock_get_service_template,
    mocker,
):
    mock_cancel = mocker.patch("app.job_api_client.cancel_job")
    client_request.post(
        "main.cancel_job",
        service_id=SERVICE_ONE_ID,
        job_id=fake_uuid,
        _expected_status=302,
        _expected_redirect=url_for(
            "main.service_dashboard",
            service_id=SERVICE_ONE_ID,
        ),
    )

    mock_cancel.assert_called_once_with(SERVICE_ONE_ID, fake_uuid)


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(fuzzed_uuid=st.uuids())
def test_should_not_show_cancelled_job(
    client_request, active_user_with_permissions, mock_get_cancelled_job, fuzzed_uuid
):
    client_request.get(
        "main.view_job",
        service_id=SERVICE_ONE_ID,
        job_id=fuzzed_uuid,
        _expected_status=404,
    )


@freeze_time("2016-01-01 05:00:00.000001")
def test_time_left():
    pass


def test_should_show_message_note(
    client_request,
    mock_get_service_template,
    mock_get_scheduled_job,
    mock_get_service_data_retention,
    mock_get_notifications,
    fake_uuid,
):
    page = client_request.get(
        "main.view_job",
        service_id=SERVICE_ONE_ID,
        job_id=fake_uuid,
    )

    assert normalize_spaces(page.select_one("main p.notification-status").text) == (
        'Messages are sent immediately to the cell phone carrier, but will remain in "pending" status until we hear '
        "back from the carrier they have received it and attempted deliver. More information on delivery status."
    )


def test_poll_status_endpoint(
    client_request,
    service_one,
    active_user_with_permissions,
    mock_get_service_data_retention,
    mocker,
    fake_uuid,
):
    """Test that the poll status endpoint returns only required data without notifications"""
    mock_job_status = mocker.patch("app.job_api_client.get_job_status")
    mock_job_status.return_value = {
        "total": 100,
        "delivered": 90,
        "failed": 10,
        "pending": 0,
        "finished": True,
    }

    response = client_request.get_response(
        "main.view_job_status_poll",
        service_id=service_one["id"],
        job_id=fake_uuid,
        _expected_status=200,
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["total"] == 100
    assert data["delivered"] == 90
    assert data["failed"] == 10
    assert data["pending"] == 0
    assert data["finished"] is True


def test_poll_status_with_zero_notifications(
    client_request,
    service_one,
    active_user_with_permissions,
    mock_get_service_data_retention,
    mocker,
    fake_uuid,
):
    """Test poll status endpoint handles edge case of no notifications"""
    mock_job_status = mocker.patch("app.job_api_client.get_job_status")
    mock_job_status.return_value = {
        "total": 0,
        "delivered": 0,
        "failed": 0,
        "pending": 0,
        "finished": True,
    }

    response = client_request.get_response(
        "main.view_job_status_poll",
        service_id=service_one["id"],
        job_id=fake_uuid,
        _expected_status=200,
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["total"] == 0
    assert data["pending"] == 0


def test_poll_status_endpoint_does_not_query_notifications_table(
    client_request,
    service_one,
    active_user_with_permissions,
    mock_get_service_data_retention,
    mocker,
    fake_uuid,
):
    """Critical regression test: ensure poll status endpoint never queries notifications"""
    mock_job_status = mocker.patch("app.job_api_client.get_job_status")
    mock_job_status.return_value = {
        "total": 500,
        "delivered": 300,
        "failed": 50,
        "pending": 150,
        "finished": False,
    }

    mock_get_notifications = mocker.patch(
        "app.notification_api_client.get_notifications_for_service"
    )

    response = client_request.get_response(
        "main.view_job_status_poll",
        service_id=service_one["id"],
        job_id=fake_uuid,
        _expected_status=200,
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["total"] == 500
    assert data["pending"] == 150

    mock_get_notifications.assert_not_called()
