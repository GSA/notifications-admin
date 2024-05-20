import base64
import json
from unittest.mock import ANY

import pytest
from flask import url_for

from app.main.views.register import check_invited_user_email_address_matches_expected
from app.models.user import User
from tests.conftest import normalize_spaces


def test_render_register_returns_template_with_form(
    client_request,
):
    client_request.logout()
    page = client_request.get_url("/register")

    assert page.find("input", attrs={"name": "auth_type"}).attrs["value"] == "sms_auth"
    assert page.select_one("#email_address")["spellcheck"] == "false"
    assert page.select_one("#email_address")["autocomplete"] == "email"
    assert page.select_one("#password")["autocomplete"] == "new-password"
    assert "Create an account" in page.text


def test_logged_in_user_redirects_to_account(
    client_request,
):
    client_request.get(
        "main.register",
        _expected_status=302,
        _expected_redirect=url_for("main.show_accounts_or_dashboard"),
    )


@pytest.mark.skip("Deprecated due to change to login-dot-gov-only registration")
@pytest.mark.parametrize(
    "phone_number_to_register_with",
    [
        "+12023900460",
        "+1800-555-5555",
    ],
)
@pytest.mark.parametrize(
    "password",
    [
        "the quick brown fox",
        "   the   quick   brown   fox   ",
    ],
)
def test_register_creates_new_user_and_redirects_to_continue_page(
    client_request,
    mock_send_verify_code,
    mock_register_user,
    mock_get_user_by_email_not_found,
    mock_email_is_not_already_in_use,
    mock_send_verify_email,
    mock_login,
    phone_number_to_register_with,
    password,
):
    client_request.logout()
    user_data = {
        "name": "Some One Valid",
        "email_address": "notfound@example.gsa.gov",
        "mobile_number": phone_number_to_register_with,
        "password": password,
        "auth_type": "sms_auth",
    }

    page = client_request.post(
        "main.register",
        _data=user_data,
        _follow_redirects=True,
    )

    assert (
        page.select("main p")[0].text
        == "An email has been sent to notfound@example.gsa.gov."
    )

    # mock_send_verify_email.assert_called_with(ANY, user_data["email_address"])
    # mock_register_user.assert_called_with(
    #    user_data["name"],
    #    user_data["email_address"],
    #    user_data["mobile_number"],
    #    user_data["password"],
    #    user_data["auth_type"],
    # )


def test_register_continue_handles_missing_session_sensibly(
    client_request,
):
    client_request.logout()
    # session is not set
    client_request.get(
        "main.registration_continue",
        _expected_redirect=url_for("main.show_accounts_or_dashboard"),
    )


def test_process_register_returns_200_when_mobile_number_is_invalid(
    client_request,
    mock_send_verify_code,
    mock_get_user_by_email_not_found,
    mock_login,
):
    client_request.logout()
    page = client_request.post(
        "main.register",
        _data={
            "name": "Bad Mobile",
            "email_address": "bad_mobile@example.gsa.gov",
            "mobile_number": "not good",
            "password": "validPassword!",
        },
        _expected_status=200,
    )

    assert "The string supplied did not seem to be a phone number" in page.text


def test_should_return_200_when_email_is_not_gov_uk(
    client_request,
    mock_get_organizations,
):
    client_request.logout()
    page = client_request.post(
        "main.register",
        _data={
            "name": "Firstname Lastname",
            "email_address": "bad_mobile@example.not.right",
            "mobile_number": "2020900123",
            "password": "validPassword!",
        },
        _expected_status=200,
    )

    assert (
        "Enter a public sector email address or find out who can use Notify"
        in normalize_spaces(page.select_one(".usa-error-message").text)
    )
    assert page.select_one(".usa-error-message a")["href"] == url_for("main.features")


@pytest.mark.parametrize(
    "email_address",
    [
        "notfound@example.gsa.gov",
        "example@lsquo.is.edu",
    ],
)
def test_should_add_user_details_to_session(
    client_request,
    mocker,
    mock_send_verify_code,
    mock_register_user,
    mock_get_user_by_email_not_found,
    mock_get_organizations_with_unusual_domains,
    mock_email_is_not_already_in_use,
    mock_send_verify_email,
    mock_login,
    email_address,
):
    client_request.logout()
    client_request.post(
        "main.register",
        _data={
            "name": "Test Codes",
            "email_address": email_address,
            "mobile_number": "+12023123123",
            "password": "validPassword!",
        },
    )
    with client_request.session_transaction() as session:
        assert session["user_details"]["email"] == email_address


def test_should_return_200_if_password_is_on_list_of_commonly_used_passwords(
    client_request,
    mock_get_user_by_email,
    mock_login,
):
    client_request.logout()
    page = client_request.post(
        "main.register",
        _data={
            "name": "Bad Mobile",
            "email_address": "bad_mobile@example.gsa.gov",
            "mobile_number": "+12021234123",
            "password": "password",
        },
        _expected_status=200,
    )

    assert "Choose a password that’s harder to guess" in page.text


def test_register_with_existing_email_sends_emails(
    client_request,
    api_user_active,
    mock_get_user_by_email,
    mock_send_already_registered_email,
):
    client_request.logout()
    user_data = {
        "name": "Already Hasaccount",
        "email_address": api_user_active["email_address"],
        "mobile_number": "+12025900460",
        "password": "validPassword!",
    }

    client_request.post(
        "main.register",
        _data=user_data,
        _expected_redirect=url_for("main.registration_continue"),
    )


@pytest.mark.parametrize(
    "invite_email_address", ["gov-user@gsa.gov", "non-gov-user@example.com"]
)
@pytest.mark.skip("TODO update this for new invite approach")
def test_register_from_email_auth_invite(
    client_request,
    sample_invite,
    mock_email_is_not_already_in_use,
    mock_register_user,
    mock_get_user,
    mock_send_verify_email,
    mock_send_verify_code,
    mock_accept_invite,
    mock_create_event,
    mock_add_user_to_service,
    mock_get_service,
    mock_get_invited_user_by_id,
    invite_email_address,
    service_one,
    fake_uuid,
    mocker,
):
    mocker.patch(
        "app.main.views.verify.service_api_client.retrieve_service_invite_data",
        return_value={},
    )
    client_request.logout()
    mock_login_user = mocker.patch("app.models.user.login_user")
    sample_invite["auth_type"] = "email_auth"
    sample_invite["email_address"] = invite_email_address
    with client_request.session_transaction() as session:
        session["invited_user_id"] = sample_invite["id"]
        # Prove that the user isn’t already signed in
        assert "user_id" not in session

    data = {
        "name": "invited user",
        "email_address": sample_invite["email_address"],
        "mobile_number": "2028675301",
        "password": "FSLKAJHFNvdzxgfyst",
        "service": sample_invite["service"],
        "auth_type": "email_auth",
    }

    client_request.post(
        "main.register_from_invite",
        _data=data,
        _expected_redirect=url_for(
            "main.service_dashboard",
            service_id=sample_invite["service"],
        ),
    )

    # doesn't send any 2fa code
    assert not mock_send_verify_email.called
    assert not mock_send_verify_code.called
    # creates user with email_auth set
    mock_register_user.assert_called_once_with(
        data["name"],
        data["email_address"],
        data["mobile_number"],
        data["password"],
        data["auth_type"],
    )
    # this is actually called twice, at the beginning of the function and then by the activate_user function
    mock_get_invited_user_by_id.assert_called_with(sample_invite["id"])
    mock_accept_invite.assert_called_once_with(
        sample_invite["service"], sample_invite["id"]
    )

    # just logs them in
    mock_login_user.assert_called_once_with(
        User(
            {
                "id": fake_uuid,  # This ID matches the return value of mock_register_user
                "platform_admin": False,
            }
        )
    )
    mock_add_user_to_service.assert_called_once_with(
        sample_invite["service"],
        fake_uuid,  # This ID matches the return value of mock_register_user
        {"manage_api_keys", "manage_service", "send_messages", "view_activity"},
        [],
    )

    with client_request.session_transaction() as session:
        # The user is signed in
        assert "user_id" in session
        # invited user details are still there so they can get added to the service
        assert session["invited_user_id"] == sample_invite["id"]


@pytest.mark.skip("TODO unskip asap")
def test_can_register_email_auth_without_phone_number(
    client_request,
    sample_invite,
    mock_email_is_not_already_in_use,
    mock_register_user,
    mock_get_user,
    mock_send_verify_email,
    mock_send_verify_code,
    mock_accept_invite,
    mock_create_event,
    mock_add_user_to_service,
    mock_get_service,
    mock_get_invited_user_by_id,
    mocker,
):
    mocker.patch(
        "app.main.views.verify.service_api_client.retrieve_service_invite_data",
        return_value={},
    )
    client_request.logout()
    sample_invite["auth_type"] = "email_auth"
    with client_request.session_transaction() as session:
        session["invited_user_id"] = sample_invite["id"]

    data = {
        "name": "invited user",
        "email_address": sample_invite["email_address"],
        "mobile_number": "",
        "password": "FSLKAJHFNvdzxgfyst",
        "service": sample_invite["service"],
        "auth_type": "email_auth",
    }

    client_request.post(
        "main.register_from_invite",
        _data=data,
        _expected_redirect=url_for(
            "main.service_dashboard",
            service_id=sample_invite["service"],
        ),
    )

    mock_register_user.assert_called_once_with(
        ANY, ANY, None, ANY, ANY  # mobile_number
    )


def test_cannot_register_with_sms_auth_and_missing_mobile_number(
    client_request,
    mock_send_verify_code,
    mock_get_user_by_email_not_found,
    mock_login,
):
    client_request.logout()
    page = client_request.post(
        "main.register",
        _data={
            "name": "Missing Mobile",
            "email_address": "missing_mobile@example.gsa.gov",
            "password": "validPassword!",
        },
        _expected_status=200,
    )

    err = page.select_one(".usa-error-message")
    assert err.text.strip() == "Error: Cannot be empty"
    assert err.attrs["data-error-label"] == "mobile_number"


def test_check_invited_user_email_address_matches_expected(mocker):
    mock_flash = mocker.patch("app.main.views.register.flash")
    mock_abort = mocker.patch("app.main.views.register.abort")

    check_invited_user_email_address_matches_expected("fake@fake.gov", "Fake@Fake.GOV")
    mock_flash.assert_not_called()
    mock_abort.assert_not_called()


def test_check_invited_user_email_address_doesnt_match_expected(mocker):
    mock_flash = mocker.patch("app.main.views.register.flash")
    mock_abort = mocker.patch("app.main.views.register.abort")

    check_invited_user_email_address_matches_expected("real@fake.gov", "Fake@Fake.GOV")
    mock_flash.assert_called_once_with(
        "You cannot accept an invite for another person."
    )
    mock_abort.assert_called_once_with(403)


def test_check_user_email_address_fails_if_not_government_address(mocker):
    mock_flash = mocker.patch("app.main.views.register.flash")
    mock_abort = mocker.patch("app.main.views.register.abort")

    check_invited_user_email_address_matches_expected(
        "fake@fake.bogus", "Fake@Fake.BOGUS"
    )
    mock_flash.assert_called_once_with("You must use a government email address.")
    mock_abort.assert_called_once_with(403)


def test_check_user_email_address_succeeds_if_government_address(mocker):
    mock_flash = mocker.patch("app.main.views.register.flash")
    mock_abort = mocker.patch("app.main.views.register.abort")

    check_invited_user_email_address_matches_expected("fake@fake.mil", "Fake@Fake.MIL")
    mock_flash.assert_not_called()
    mock_abort.assert_not_called()


def decode_invite_data(state):
    state = state.encode("utf8")
    state = base64.b64decode(state)
    state = json.loads(state)
    return state


# Test that we can successfully decode the invited user
# data that is sent in the state param
def test_decode_state(encoded_invite_data):
    assert decode_invite_data(encoded_invite_data) == {
        "folder_permissions": [],
        "from_user_id": "xyz",
        "invited_user_id": "invited_user",
        "permissions": ["manage_everything"],
        "service_id": "service",
    }
