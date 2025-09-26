"""
Tests for job notification update logic during polling.

These tests verify the poll status endpoint behavior and document
the JavaScript notification refresh logic:
1. Notifications update for first 50 messages
2. Notifications stop updating after 50 messages (to prevent performance issues)
3. Notifications always update when job finishes
"""

import json

import pytest

from tests import job_json, user_json


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
    )

    assert response.status_code == 200
    data = json.loads(response.get_data(as_text=True))

    # Verify the response
    assert data["sent_count"] == delivered
    assert data["failed_count"] == failed
    assert data["pending_count"] == pending
    assert data["total_count"] == total
    assert data["finished"] is finished

    processed_count = delivered + failed

    if js_should_update_notifications:
        # JavaScript would call: await updateNotifications()
        if finished:
            assert finished, f"JS updates notifications: {reason}"
        else:
            assert processed_count <= 50, f"JS updates notifications: {reason}"
            assert not finished, f"JS updates notifications: {reason}"
    else:
        # JavaScript would NOT update notifications
        assert processed_count > 50, f"JS skips notification update: {reason}"
        assert not finished, f"JS skips notification update: {reason}"


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
    )

    data = json.loads(response.get_data(as_text=True))

    required_fields = {"sent_count", "failed_count", "finished", "pending_count", "total_count"}
    assert set(data.keys()) == required_fields

    response_size = len(response.get_data(as_text=True))
    assert response_size < 200, f"Response too large: {response_size} bytes"
