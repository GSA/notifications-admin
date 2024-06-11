import uuid

import pytest
from flask import url_for

from app.main.views.sign_in import _reformat_keystring
from app.models.user import User
from tests.conftest import SERVICE_ONE_ID, normalize_spaces


def test_render_sign_in_template_for_new_user(client_request):
    client_request.logout()
    page = client_request.get("main.sign_in")
    assert normalize_spaces(page.select_one("h1").text) == "Sign in"
    assert (
        page.select("main p")[0].text
        == "Access your Notify.gov account by signing in with Login.gov:"
    )
    # TODO:  Fix this test to be less brittle! If the Login.gov link is enabled,
    #        then these indices need to be 1 instead of 0.
    #        Currently it's not enabled for the test or production environments.
    assert page.select("main a")[0].text == "Sign in with Login.gov"

    # TODO:  We'll have to adjust this depending on whether Login.gov is
    #        enabled or not; fix this in the future.
    assert "Sign in again" not in normalize_spaces(page.text)


def test_sign_in_explains_session_timeout(client_request):
    client_request.logout()
    page = client_request.get("main.sign_in", next="/foo")
    assert (
        "We signed you out because you have not used Notify for a while." in page.text
    )


def test_doesnt_redirect_to_sign_in_if_no_session_info(
    client_request,
    api_user_active,
    mock_get_organization_by_domain,
):
    api_user_active["current_session_id"] = str(uuid.UUID(int=1))

    with client_request.session_transaction() as session:
        session["current_session_id"] = None

    with client_request.session_transaction() as session:
        session["current_session_id"] = None

    client_request.get("main.add_service")


def test_logged_in_user_redirects_to_account(client_request):
    client_request.get(
        "main.sign_in",
        _expected_status=302,
        _expected_redirect=url_for("main.show_accounts_or_dashboard"),
    )


def test_logged_in_user_redirects_to_next_url(client_request):
    client_request.get(
        "main.sign_in",
        next="/user-profile",
        _expected_status=302,
        _expected_redirect=url_for("main.user_profile"),
    )


def test_logged_in_user_doesnt_do_evil_redirect(client_request):
    client_request.get(
        "main.sign_in",
        next="http://www.evil.com",
        _expected_status=302,
        _expected_redirect=url_for("main.show_accounts_or_dashboard"),
    )


@pytest.mark.skip("TODO is this still relevant post login.gov switch?")
def test_should_return_redirect_when_user_is_pending(
    client_request,
    mock_get_user_by_email_pending,
    api_user_pending,
    mock_verify_password,
):
    client_request.logout()
    client_request.post(
        "main.sign_in",
        _data={
            "email_address": "pending_user@example.gsa.gov",
            "password": "val1dPassw0rd!",
        },
        _expected_redirect=url_for("main.resend_email_verification"),
    )
    with client_request.session_transaction() as s:
        assert s["user_details"] == {
            "email": api_user_pending["email_address"],
            "id": api_user_pending["id"],
        }


@pytest.mark.parametrize(
    "redirect_url",
    [
        None,
        f"/services/{SERVICE_ONE_ID}/templates",
    ],
)
@pytest.mark.skip("TODO is this still relevant post login.gov switch?")
def test_should_attempt_redirect_when_user_is_pending(
    client_request, mock_get_user_by_email_pending, mock_verify_password, redirect_url
):
    client_request.logout()
    client_request.post(
        "main.sign_in",
        next=redirect_url,
        _data={
            "email_address": "pending_user@example.gsa.gov",
            "password": "val1dPassw0rd!",
        },
        _expected_redirect=url_for("main.resend_email_verification", next=redirect_url),
    )


@pytest.mark.skip("TODO move this to register and update with login.gov")
def test_when_signing_in_as_invited_user_you_cannot_accept_an_invite_for_another_email_address(
    client_request,
    mocker,
    mock_verify_password,
    api_user_active,
    sample_invite,
    mock_accept_invite,
    mock_send_verify_code,
    mock_get_invited_user_by_id,
):
    sample_invite["email_address"] = "some_other_user@user.gsa.gov"

    mocker.patch(
        "app.models.user.User.from_email_address_and_password_or_none",
        return_value=User(api_user_active),
    )

    client_request.logout()

    with client_request.session_transaction() as session:
        session["invited_user_id"] = sample_invite["id"]

    page = client_request.post(
        "main.sign_in",
        _data={"email_address": "test@user.gsa.gov", "password": "val1dPassw0rd!"},
        _expected_status=403,
    )

    assert mock_accept_invite.called is False
    assert mock_send_verify_code.called is False
    assert (
        page.select_one(".banner-dangerous").text.strip()
        == "You cannot accept an invite for another person."
    )
