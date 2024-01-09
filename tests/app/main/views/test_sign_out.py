from tests.conftest import SERVICE_ONE_ID

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
                "name": "grsrbsrgsrf",
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
                "name": "personalized",
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

MOCK_ONE_OFF_JOB = {
    "data": {
        "api_key": "mocked_api_key",
        "billable_units": 1,
        "carrier": "mocked_carrier",
        "client_reference": "mocked_client_reference",
        "created_at": "2024-01-04T20:43:52+00:00",
        "created_by": {
            "email_address": "mocked_email@example.com",
            "id": "mocked_user_id",
            "name": "mocked_user",
        },
        "document_download_count": None,
        "id": "mocked_notification_id",
        "international": False,
        "job": {"id": "mocked_job_id", "original_file_name": "mocked_file.txt"},
        "job_row_number": 0,
        "key_name": "mocked_key_name",
        "key_type": "normal",
        "normalised_to": "+12133166548",
        "notification_type": "sms",
        "personalisation": {"phonenumber": "+12133166548"},
        "phone_prefix": "1",
        "provider_response": "mocked_provider_response",
        "rate_multiplier": 1.0,
        "reference": "mocked_reference",
        "reply_to_text": "mocked_reply_text",
        "sent_at": "2024-01-04T20:43:53+00:00",
        "sent_by": "mocked_sender",
        "service": "mocked_service_id",
        "status": "sending",
        "template": {
            "content": "((day of week)) and ((fave color))",
            "id": "bd9caa7e-00ee-4c5a-839e-10ae1a7e6f73",
            "name": "personalized",
            "redact_personalisation": False,
            "subject": None,
            "template_type": "sms",
            "version": 1,
        },
        "to": "+12133166548",
        "updated_at": "2024-01-04T20:43:53+00:00",
    }
}


def test_render_sign_out_redirects_to_sign_in(client_request):
    # TODO with the change to using login.gov, we no longer redirect directly to the sign in page.
    # Instead we redirect to login.gov which redirects us to the sign in page.  However, the
    # test for the expected redirect being "/" is buried in conftest and looks fragile.
    # After we move to login.gov officially and get rid of other forms of signing it, it should
    # be refactored.
    with client_request.session_transaction() as session:
        assert session
    client_request.get(
        "main.sign_out",
        _expected_status=302,
    )
    with client_request.session_transaction() as session:
        assert not session


def test_sign_out_user(
    mocker,
    client_request,
    mock_get_service,
    api_user_active,
    mock_get_user,
    mock_get_user_by_email,
    mock_login,
    mock_get_service_templates,
    mock_has_no_jobs,
    mock_has_permissions,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    with client_request.session_transaction() as session:
        assert session.get("user_id") is not None
    # Check we are logged in
    mocker.patch("app.job_api_client.get_job", return_value=MOCK_ONE_OFF_JOB)

    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )

    client_request.get(
        "main.service_dashboard",
        service_id=SERVICE_ONE_ID,
    )
    client_request.get(
        "main.sign_out",
        _expected_status=302,
    )
    with client_request.session_transaction() as session:
        assert session.get("user_id") is None


def test_sign_out_of_two_sessions(client_request):
    client_request.get(
        "main.sign_out",
        _expected_status=302,
    )
    with client_request.session_transaction() as session:
        assert not session
    client_request.get(
        "main.sign_out",
        _expected_status=302,
    )
