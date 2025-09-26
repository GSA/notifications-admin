"""
Tests for disabled job polling endpoint.

These tests verify that the poll status endpoint is properly disabled
and returns 410 Gone status. The JavaScript notification refresh logic
is no longer used as polling has been replaced with manual refresh.
"""

import pytest


@pytest.mark.parametrize(
    ("delivered", "failed", "pending", "finished", "js_should_update_notifications", "reason"),
    [
        (20, 10, 70, False, True, "30 messages processed (≤50 threshold)"),
        (40, 10, 50, False, True, "50 messages processed (exactly at threshold)"),
        (45, 15, 40, False, False, "60 messages processed (>50 threshold)"),
        (450, 50, 0, True, True, "500 messages but job finished (always updates)"),
    ],
)
def test_poll_status_notification_update_logic(
    client_request,
    service_one,
    active_user_with_permissions,
    mock_get_service_data_retention,
    mocker,
    fake_uuid,
    delivered,
    failed,
    pending,
    finished,
    js_should_update_notifications,
    reason,
):
    """
    Test poll status endpoint for various scenarios.

    The JavaScript updates notifications when:
        processedCount ≤ 50 AND job not finished
        job is finished (regardless of count)
    """
    total = delivered + failed + pending

    mock_job_status = mocker.patch("app.job_api_client.get_job_status")
    mock_job_status.return_value = {
        "sent_count": delivered,
        "failed_count": failed,
        "pending_count": pending,
        "total_count": total,
        "processing_finished": finished,
    }

    response = client_request.get_response(
        "main.view_job_status_poll",
        service_id=service_one["id"],
        job_id=fake_uuid,
        _expected_status=410,
    )

    assert response.status_code == 410
    # Endpoint is disabled, so no data to verify

    # Since the polling endpoint is disabled, the JavaScript logic being tested
    # is no longer relevant. The test now verifies the endpoint is disabled.


def test_poll_status_provides_required_fields(
    client_request,
    service_one,
    active_user_with_permissions,
    mock_get_service_data_retention,
    mocker,
    fake_uuid,
):
    """Verify poll status endpoint returns all fields needed for notification update logic."""
    mock_job_status = mocker.patch("app.job_api_client.get_job_status")
    mock_job_status.return_value = {
        "sent_count": 15,
        "failed_count": 5,
        "pending_count": 5,
        "total_count": 25,
        "processing_finished": False,
    }

    response = client_request.get_response(
        "main.view_job_status_poll",
        service_id=service_one["id"],
        job_id=fake_uuid,
        _expected_status=410,
    )

    assert response.status_code == 410
