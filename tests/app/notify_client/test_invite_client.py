from unittest.mock import ANY

from flask import current_app

from app import invite_api_client


def test_client_creates_invite(
    notify_admin,
    mocker,
    fake_uuid,
    sample_invite,
):
    mocker.patch("app.notify_client.current_user")

    mock_post = mocker.patch(
        "app.invite_api_client.post",
        return_value={
            "data": dict.fromkeys(
                {
                    "id",
                    "service",
                    "from_user",
                    "email_address",
                    "permissions",
                    "status",
                    "created_at",
                    "auth_type",
                    "folder_permissions",
                    "nonce",
                    "state",
                }
            )
        },
    )

    mock_token_urlsafe = mocker.patch("secrets.token_urlsafe")
    fake_nonce = "1234567890"
    fake_state = "0987654321"
    mock_token_urlsafe.return_value = fake_nonce

    mock_generate_token = mocker.patch(
        "app.notify_client.invite_api_client.generate_token"
    )
    mock_generate_token.return_value = fake_state

    with current_app.test_request_context("/whatever"):
        invite_api_client.create_invite(
            "12345",
            "67890",
            "test@example.com",
            {"send_messages"},
            "sms_auth",
            [fake_uuid],
        )

    mock_post.assert_called_once_with(
        url=f"/service/{"67890"}/invite",
        data={
            "auth_type": "sms_auth",
            "email_address": "test@example.com",
            "from_user": "12345",
            "service": "67890",
            "created_by": ANY,
            "permissions": "send_emails,send_texts",
            "invite_link_host": "http://localhost:6012",
            "folder_permissions": [fake_uuid],
            "nonce": fake_nonce,
            "state": fake_state,
        },
    )


def test_client_returns_invite(mocker, sample_invite):
    sample_invite["status"] = "pending"
    service_id = sample_invite["service"]

    expected_data = {"data": [sample_invite]}

    expected_url = "/service/{}/invite".format(service_id)

    mock_get = mocker.patch(
        "app.notify_client.invite_api_client.InviteApiClient.get",
        return_value=expected_data,
    )

    invites = invite_api_client.get_invites_for_service(service_id)

    mock_get.assert_called_once_with(expected_url)
    assert len(invites) == 1
    assert invites[0]["status"] == "pending"
