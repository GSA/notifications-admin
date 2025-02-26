from unittest.mock import ANY, Mock, call

import pytest
from flask import url_for
from freezegun import freeze_time
from notifications_python_client.errors import HTTPError

import app
from tests import service_json
from tests.conftest import (
    SERVICE_ONE_ID,
    create_active_caseworking_user,
    create_active_user_with_permissions,
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

MOCK_JOBS = {
    "data": [
        {
            "archived": False,
            "created_at": "2024-01-04T20:43:52+00:00",
            "created_by": {
                "id": "mocked_user_id",
                "name": "mocked_user",
            },
            "id": "mocked_notification_id",
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


@pytest.fixture
def _mock_no_users_for_service(mocker):
    mocker.patch("app.models.user.Users.client_method", return_value=[])


@pytest.fixture
def mock_get_existing_user_by_email(mocker, api_user_active):
    return mocker.patch(
        "app.user_api_client.get_user_by_email", return_value=api_user_active
    )


@pytest.fixture
def mock_check_invite_token(mocker, sample_invite):
    return mocker.patch("app.invite_api_client.check_token", return_value=sample_invite)


@pytest.mark.usefixtures("_mock_no_users_for_service")
@freeze_time("2021-12-12 12:12:12")
def test_existing_user_accept_invite_calls_api_and_redirects_to_dashboard(
    client_request,
    service_one,
    api_user_active,
    mock_check_invite_token,
    mock_get_existing_user_by_email,
    mock_accept_invite,
    mock_add_user_to_service,
    mock_get_service,
    mocker,
    mock_events,
    mock_get_user,
    mock_update_user_attribute,
):

    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()
    expected_service = service_one["id"]
    expected_permissions = {
        "view_activity",
        "send_messages",
        "manage_service",
        "manage_api_keys",
    }

    client_request.get(
        "main.accept_invite",
        token="thisisnotarealtoken",
        _expected_redirect=url_for(
            "main.service_dashboard", service_id=expected_service
        ),
    )

    mock_check_invite_token.assert_called_with("thisisnotarealtoken")
    mock_get_existing_user_by_email.assert_called_with("invited_user@test.gsa.gov")
    assert mock_accept_invite.call_count == 1
    mock_add_user_to_service.assert_called_with(
        expected_service,
        api_user_active["id"],
        expected_permissions,
        [],
    )


@pytest.mark.usefixtures("_mock_no_users_for_service")
def test_existing_user_with_no_permissions_or_folder_permissions_accept_invite(
    client_request,
    mocker,
    service_one,
    api_user_active,
    sample_invite,
    mock_check_invite_token,
    mock_get_existing_user_by_email,
    mock_add_user_to_service,
    mock_get_service,
    mock_events,
    mock_get_user,
    mock_update_user_attribute,
):

    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()

    expected_service = service_one["id"]
    sample_invite["permissions"] = ""
    expected_permissions = set()
    expected_folder_permissions = []
    mocker.patch("app.invite_api_client.accept_invite", return_value=sample_invite)

    client_request.get(
        "main.accept_invite",
        token="thisisnotarealtoken",
        _expected_status=302,
    )
    mock_add_user_to_service.assert_called_with(
        expected_service,
        api_user_active["id"],
        expected_permissions,
        expected_folder_permissions,
    )


def test_if_existing_user_accepts_twice_they_redirect_to_sign_in(
    client_request,
    mocker,
    sample_invite,
    mock_check_invite_token,
    mock_get_service,
    mock_update_user_attribute,
):

    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()
    # Logging out updates the current session ID to `None`
    mock_update_user_attribute.reset_mock()
    sample_invite["status"] = "accepted"

    page = client_request.get(
        "main.accept_invite",
        token="thisisnotarealtoken",
        _follow_redirects=True,
    )

    assert (
        page.h1.string,
        page.select("main p")[0].text.strip(),
    ) == (
        "You need to sign in again",
        # TODO:  Improve this given Login.gov configuration.
        "We signed you out because you have not used Notify for a while.",
    )
    # We don’t let people update `email_access_validated_at` using an
    # already-accepted invite
    assert mock_update_user_attribute.called is False


@pytest.mark.usefixtures("_mock_no_users_for_service")
def test_invite_goes_in_session(
    client_request,
    mocker,
    sample_invite,
    mock_get_service,
    api_user_active,
    mock_check_invite_token,
    mock_get_user_by_email,
    mock_add_user_to_service,
    mock_accept_invite,
):
    sample_invite["email_address"] = "test@user.gsa.gov"

    client_request.get(
        "main.accept_invite",
        token="thisisnotarealtoken",
        _expected_status=302,
        _expected_redirect=url_for(
            "main.service_dashboard",
            service_id=SERVICE_ONE_ID,
        ),
        _follow_redirects=False,
    )

    with client_request.session_transaction() as session:
        assert session["invited_user_id"] == sample_invite["id"]


@pytest.mark.usefixtures("_mock_no_users_for_service")
@pytest.mark.parametrize(
    ("user", "landing_page_title"),
    [
        (create_active_user_with_permissions(), "Dashboard"),
        (create_active_caseworking_user(), "Select or create a template"),
    ],
)
def test_accepting_invite_removes_invite_from_session(
    client_request,
    mocker,
    sample_invite,
    mock_get_service,
    service_one,
    mock_check_invite_token,
    mock_get_user_by_email,
    mock_add_user_to_service,
    mock_accept_invite,
    mock_get_service_templates,
    mock_get_template_statistics,
    mock_has_no_jobs,
    mock_get_service_statistics,
    mock_get_template_folders,
    mock_get_annual_usage_for_service,
    mock_get_monthly_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
    mock_get_api_keys,
    fake_uuid,
    user,
    landing_page_title,
):
    sample_invite["email_address"] = user["email_address"]

    client_request.login(user)
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    date_range = {"start_date": "2024-01-01", "days": 7}

    mocker.patch(
        "app.main.views.dashboard.get_daily_stats",
        return_value={
            date_range["start_date"]: {
                "email": {"delivered": 0, "failure": 0, "requested": 0},
                "sms": {"delivered": 0, "failure": 1, "requested": 1},
            },
        },
    )

    mocker.patch(
        "app.main.views.dashboard.get_daily_stats_by_user",
        return_value={
            date_range["start_date"]: {
                "email": {"delivered": 1, "failure": 0, "requested": 1},
                "sms": {"delivered": 1, "failure": 0, "requested": 1},
            },
        },
    )

    mocker.patch(
        "app.service_api_client.get_service_message_ratio",
        return_value={
            "messages_remaining": 71919,
            "messages_sent": 28081,
            "total_message_limit": 100000
        },
    )
    page = client_request.get(
        "main.accept_invite",
        token="thisisnotarealtoken",
        _follow_redirects=True,
    )
    assert normalize_spaces(page.select_one("h1").text) == landing_page_title

    with client_request.session_transaction() as session:
        assert "invited_user_id" not in session


@freeze_time("2021-12-12T12:12:12")
def test_existing_user_of_service_get_redirected_to_signin(
    client_request,
    mocker,
    api_user_active,
    sample_invite,
    mock_get_service,
    mock_get_user_by_email,
    mock_check_invite_token,
    mock_accept_invite,
    mock_update_user_attribute,
):

    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()
    sample_invite["email_address"] = api_user_active["email_address"]
    mocker.patch("app.models.user.Users.client_method", return_value=[api_user_active])

    page = client_request.get(
        "main.accept_invite",
        token="thisisnotarealtoken",
        _follow_redirects=True,
    )

    assert (
        page.h1.string,
        page.select("main p")[0].text.strip(),
    ) == (
        "You need to sign in again",
        # TODO:  Improve this given Login.gov configuration.
        "We signed you out because you have not used Notify for a while.",
    )
    assert mock_accept_invite.call_count == 1


@pytest.mark.usefixtures("_mock_no_users_for_service")
def test_accept_invite_redirects_if_api_raises_an_error_that_they_are_already_part_of_the_service(
    client_request,
    mocker,
    api_user_active,
    sample_invite,
    mock_get_existing_user_by_email,
    mock_check_invite_token,
    mock_accept_invite,
    mock_get_service,
    mock_get_user,
    mock_update_user_attribute,
):

    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()

    mocker.patch(
        "app.user_api_client.add_user_to_service",
        side_effect=HTTPError(
            response=Mock(
                status_code=400,
                json={
                    "result": "error",
                    "message": {
                        f"User id: {api_user_active['id']} already part of service id: {SERVICE_ONE_ID}"
                    },
                },
            ),
            message=f"User id: {api_user_active['id']} already part of service id: {SERVICE_ONE_ID}",
        ),
    )

    client_request.get(
        "main.accept_invite",
        token="thisisnotarealtoken",
        _follow_redirects=False,
        _expected_redirect=url_for("main.service_dashboard", service_id=SERVICE_ONE_ID),
    )


@pytest.mark.usefixtures("_mock_no_users_for_service")
def test_existing_signed_out_user_accept_invite_redirects_to_sign_in(
    client_request,
    service_one,
    api_user_active,
    sample_invite,
    mock_check_invite_token,
    mock_get_existing_user_by_email,
    mock_add_user_to_service,
    mock_accept_invite,
    mock_get_service,
    mocker,
    mock_events,
    mock_get_user,
    mock_update_user_attribute,
):

    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()
    expected_service = service_one["id"]
    expected_permissions = {
        "view_activity",
        "send_messages",
        "manage_service",
        "manage_api_keys",
    }

    page = client_request.get(
        "main.accept_invite",
        token="thisisnotarealtoken",
        _follow_redirects=True,
    )

    mock_check_invite_token.assert_called_with("thisisnotarealtoken")
    mock_get_existing_user_by_email.assert_called_with("invited_user@test.gsa.gov")
    mock_add_user_to_service.assert_called_with(
        expected_service,
        api_user_active["id"],
        expected_permissions,
        sample_invite["folder_permissions"],
    )
    assert mock_accept_invite.call_count == 1
    assert (
        page.h1.string,
        page.select("main p")[0].text.strip(),
    ) == (
        "You need to sign in again",
        # TODO:  Improve this given Login.gov configuration.
        "We signed you out because you have not used Notify for a while.",
    )


def test_cancelled_invited_user_accepts_invited_redirect_to_cancelled_invitation(
    client_request,
    mock_get_user,
    mock_get_service,
    sample_invite,
    mock_check_invite_token,
    mock_update_user_attribute,
    mocker,
):

    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()
    mock_update_user_attribute.reset_mock()
    sample_invite["status"] = "cancelled"
    page = client_request.get("main.accept_invite", token="thisisnotarealtoken")

    app.invite_api_client.check_token.assert_called_with("thisisnotarealtoken")

    assert page.h1.string.strip() == "The invitation you were sent has been cancelled"
    # We don’t let people update `email_access_validated_at` using an
    # cancelled invite
    assert mock_update_user_attribute.called is False


@pytest.mark.parametrize(
    ("admin_endpoint", "api_endpoint"),
    [
        ("main.accept_invite", "app.invite_api_client.check_token"),
        ("main.accept_org_invite", "app.org_invite_api_client.check_token"),
    ],
)
def test_new_user_accept_invite_with_malformed_token(
    admin_endpoint,
    api_endpoint,
    client_request,
    service_one,
    mocker,
):

    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()
    mocker.patch(
        api_endpoint,
        side_effect=HTTPError(
            response=Mock(
                status_code=400,
                json={
                    "result": "error",
                    "message": {
                        "invitation": {
                            "Something’s wrong with this link. Make sure you’ve copied the whole thing."
                        }
                    },
                },
            ),
            message={
                "invitation": "Something’s wrong with this link. Make sure you’ve copied the whole thing."
            },
        ),
    )

    page = client_request.get(
        admin_endpoint, token="thisisnotarealtoken", _follow_redirects=True
    )

    assert (
        normalize_spaces(page.select_one(".banner-dangerous").text)
        == "Something’s wrong with this link. Make sure you’ve copied the whole thing."
    )


def test_signed_in_existing_user_cannot_use_anothers_invite(
    client_request,
    mocker,
    api_user_active,
    mock_check_invite_token,
    sample_invite,
    mock_get_user,
    mock_accept_invite,
    mock_get_service,
):
    mocker.patch(
        "app.user_api_client.get_users_for_service", return_value=[api_user_active]
    )

    page = client_request.get(
        "main.accept_invite",
        token="thisisnotarealtoken",
        _follow_redirects=True,
        _expected_status=403,
    )
    assert page.h1.string.strip() == "You’re not allowed to see this page"
    flash_banners = page.find_all("div", class_="banner-dangerous")
    assert len(flash_banners) == 1
    banner_contents = normalize_spaces(flash_banners[0].text)
    assert "You’re signed in as test@user.gsa.gov." in banner_contents
    assert "This invite is for another email address." in banner_contents
    assert "Sign out and click the link again to accept this invite." in banner_contents
    assert mock_accept_invite.call_count == 0


def test_accept_invite_does_not_treat_email_addresses_as_case_sensitive(
    client_request,
    mocker,
    api_user_active,
    sample_invite,
    mock_accept_invite,
    mock_check_invite_token,
    mock_get_user_by_email,
):
    # the email address of api_user_active is 'test@user.gsa.gov'
    sample_invite["email_address"] = "TEST@user.gsa.gov"
    mocker.patch("app.models.user.Users.client_method", return_value=[api_user_active])

    client_request.get(
        "main.accept_invite",
        token="thisisnotarealtoken",
        _expected_status=302,
        _expected_redirect=url_for(
            "main.service_dashboard",
            service_id=SERVICE_ONE_ID,
        ),
    )


@pytest.mark.skip("TODO unskip asap")
@pytest.mark.usefixtures("_mock_no_users_for_service")
def test_new_invited_user_verifies_and_added_to_service(
    client_request,
    service_one,
    sample_invite,
    api_user_active,
    mock_check_invite_token,
    mock_dont_get_user_by_email,
    mock_email_is_not_already_in_use,
    mock_register_user,
    mock_send_verify_code,
    mock_check_verify_code,
    mock_get_user,
    mock_update_user_attribute,
    mock_add_user_to_service,
    mock_accept_invite,
    mock_get_service,
    mock_get_invited_user_by_id,
    mock_get_service_templates,
    mock_get_template_statistics,
    mock_has_no_jobs,
    mock_has_permissions,
    mock_get_service_statistics,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_create_event,
    mocker,
):

    mocker.patch(
        "app.main.views.verify.service_api_client.retrieve_service_invite_data",
        return_value={},
    )

    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()

    # visit accept token page
    client_request.get(
        "main.accept_invite",
        token="thisisnotarealtoken",
        _expected_redirect=url_for("main.register_from_invite"),
    )
    mocker.patch("app.job_api_client.get_jobs", return_value=MOCK_JOBS)
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )

    # get redirected to register from invite
    data = {
        "service": sample_invite["service"],
        "email_address": sample_invite["email_address"],
        "from_user": sample_invite["from_user"],
        "password": "longpassword",  # noqa
        "mobile_number": "+12027890123",
        "name": "Invited User",
        "auth_type": "sms_auth",
    }
    client_request.post(
        "main.register_from_invite",
        _data=data,
        _expected_redirect=url_for("main.verify"),
    )

    # that sends user on to verify
    page = client_request.post(
        "main.verify",
        _data={"sms_code": "123456"},
        _follow_redirects=True,
    )

    # when they post codes back to admin user should be added to
    # service and sent on to dash board
    expected_permissions = {
        "view_activity",
        "send_messages",
        "manage_service",
        "manage_api_keys",
    }

    with client_request.session_transaction() as session:
        assert "invited_user_id" not in session
        new_user_id = session["user_id"]
        mock_add_user_to_service.assert_called_with(
            data["service"], new_user_id, expected_permissions, []
        )
        mock_accept_invite.assert_called_with(data["service"], sample_invite["id"])
        mock_check_verify_code.assert_called_once_with(new_user_id, "123456", "sms")
        assert service_one["id"] == session["service_id"]

    assert page.find("h1").text == "Dashboard"


@pytest.mark.parametrize(
    ("service_permissions", "trial_mode", "expected_endpoint", "extra_args"),
    [
        ([], True, "main.service_dashboard", {}),
        ([], False, "main.service_dashboard", {}),
    ],
)
@pytest.mark.skip("TODO unskip asap")
def test_new_invited_user_is_redirected_to_correct_place(
    mocker,
    client_request,
    sample_invite,
    mock_check_invite_token,
    mock_check_verify_code,
    mock_get_user,
    mock_dont_get_user_by_email,
    mock_add_user_to_service,
    mock_get_invited_user_by_id,
    mock_events,
    mock_get_service,
    service_permissions,
    trial_mode,
    expected_endpoint,
    extra_args,
):
    mocker.patch(
        "app.main.views.verify.service_api_client.retrieve_service_invite_data",
        return_value={},
    )

    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()
    mocker.patch(
        "app.service_api_client.get_service",
        return_value={
            "data": service_json(
                sample_invite["service"],
                restricted=trial_mode,
                permissions=service_permissions,
            )
        },
    )
    client_request.get(
        "main.accept_invite",
        token="thisisnotarealtoken",
        _expected_status=302,
    )

    with client_request.session_transaction() as session:
        session["user_details"] = {
            "email": sample_invite["email_address"],
            "id": sample_invite["id"],
        }

    client_request.post(
        "main.verify",
        _data={"sms_code": "123456"},
        _expected_redirect=url_for(
            expected_endpoint, service_id=sample_invite["service"], **extra_args
        ),
    )


@pytest.mark.usefixtures("_mock_no_users_for_service")
@freeze_time("2021-12-12 12:12:12")
def test_existing_user_accepts_and_sets_email_auth(
    client_request,
    api_user_active,
    service_one,
    sample_invite,
    mock_get_existing_user_by_email,
    mock_accept_invite,
    mock_check_invite_token,
    mock_update_user_attribute,
    mock_add_user_to_service,
    mocker,
):
    sample_invite["email_address"] = api_user_active["email_address"]

    service_one["permissions"].append("email_auth")
    sample_invite["auth_type"] = "email_auth"

    client_request.get(
        "main.accept_invite",
        token="thisisnotarealtoken",
        _expected_status=302,
        _expected_redirect=url_for(
            "main.service_dashboard", service_id=service_one["id"]
        ),
    )

    mock_get_existing_user_by_email.assert_called_once_with("test@user.gsa.gov")
    assert mock_update_user_attribute.call_args_list == [
        call(api_user_active["id"], email_access_validated_at="2021-12-12T12:12:12"),
        call(api_user_active["id"], auth_type="email_auth"),
    ]
    mock_add_user_to_service.assert_called_once_with(
        ANY, api_user_active["id"], ANY, ANY
    )


@pytest.mark.usefixtures("_mock_no_users_for_service")
@freeze_time("2021-12-12 12:12:12")
def test_platform_admin_user_accepts_and_preserves_auth(
    client_request,
    platform_admin_user,
    service_one,
    sample_invite,
    mock_check_invite_token,
    mock_accept_invite,
    mock_add_user_to_service,
    mocker,
):
    sample_invite["email_address"] = platform_admin_user["email_address"]
    sample_invite["auth_type"] = "email_auth"
    service_one["permissions"].append("email_auth")

    mocker.patch(
        "app.user_api_client.get_user_by_email", return_value=platform_admin_user
    )
    mock_update_user_attribute = mocker.patch(
        "app.user_api_client.update_user_attribute",
        return_value=platform_admin_user,
    )

    client_request.login(platform_admin_user)

    client_request.get(
        "main.accept_invite",
        token="thisisnotarealtoken",
        _expected_status=302,
        _expected_redirect=url_for(
            "main.service_dashboard", service_id=service_one["id"]
        ),
    )

    mock_update_user_attribute.assert_called_once_with(
        platform_admin_user["id"],
        email_access_validated_at="2021-12-12T12:12:12",
    )
    assert mock_add_user_to_service.called


@pytest.mark.usefixtures("_mock_no_users_for_service")
@freeze_time("2021-12-12 12:12:12")
def test_existing_user_doesnt_get_auth_changed_by_service_without_permission(
    client_request,
    api_user_active,
    service_one,
    sample_invite,
    mock_get_user_by_email,
    mock_check_invite_token,
    mock_accept_invite,
    mock_update_user_attribute,
    mock_add_user_to_service,
    mocker,
):
    sample_invite["email_address"] = api_user_active["email_address"]

    assert "email_auth" not in service_one["permissions"]

    sample_invite["auth_type"] = "email_auth"

    client_request.get(
        "main.accept_invite",
        token="thisisnotarealtoken",
        _expected_status=302,
        _expected_redirect=url_for(
            "main.service_dashboard", service_id=service_one["id"]
        ),
    )

    mock_update_user_attribute.assert_called_once_with(
        api_user_active["id"],
        email_access_validated_at="2021-12-12T12:12:12",
    )


@pytest.mark.usefixtures("_mock_no_users_for_service")
@freeze_time("2021-12-12 12:12:12")
def test_existing_email_auth_user_without_phone_cannot_set_sms_auth(
    client_request,
    api_user_active,
    service_one,
    sample_invite,
    mock_check_invite_token,
    mock_accept_invite,
    mock_update_user_attribute,
    mock_add_user_to_service,
    mocker,
):
    sample_invite["email_address"] = api_user_active["email_address"]

    service_one["permissions"].append("email_auth")

    api_user_active["auth_type"] = "email_auth"
    api_user_active["mobile_number"] = None
    sample_invite["auth_type"] = "sms_auth"

    mocker.patch("app.user_api_client.get_user_by_email", return_value=api_user_active)

    client_request.get(
        "main.accept_invite",
        token="thisisnotarealtoken",
        _expected_status=302,
        _expected_redirect=url_for(
            "main.service_dashboard", service_id=service_one["id"]
        ),
    )

    mock_update_user_attribute.assert_called_once_with(
        api_user_active["id"],
        email_access_validated_at="2021-12-12T12:12:12",
    )


@pytest.mark.usefixtures("_mock_no_users_for_service")
@freeze_time("2021-12-12 12:12:12")
def test_existing_email_auth_user_with_phone_can_set_sms_auth(
    client_request,
    api_user_active,
    service_one,
    sample_invite,
    mock_get_existing_user_by_email,
    mock_check_invite_token,
    mock_accept_invite,
    mock_update_user_attribute,
    mock_add_user_to_service,
    mocker,
):
    sample_invite["email_address"] = api_user_active["email_address"]
    service_one["permissions"].append("email_auth")
    sample_invite["auth_type"] = "sms_auth"

    client_request.get(
        "main.accept_invite",
        token="thisisnotarealtoken",
        _expected_status=302,
        _expected_redirect=url_for(
            "main.service_dashboard", service_id=service_one["id"]
        ),
    )

    mock_get_existing_user_by_email.assert_called_once_with(
        sample_invite["email_address"]
    )
    assert mock_update_user_attribute.call_args_list == [
        call(api_user_active["id"], email_access_validated_at="2021-12-12T12:12:12"),
        call(api_user_active["id"], auth_type="sms_auth"),
    ]
