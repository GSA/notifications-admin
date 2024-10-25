import os
from functools import partial

import pytest
from bs4 import BeautifulSoup
from flask import url_for
from freezegun import freeze_time

from tests.conftest import SERVICE_ONE_ID, normalize_spaces

def test_non_logged_in_user_can_see_homepage(
    client_request, mock_get_service_and_organization_counts, mocker
):

    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()
    page = client_request.get("main.index", _test_page_title=False)

    assert page.h1.text.strip() == (
        "Reach people where they are with government-powered text messages"
    )

    assert (
        page.select_one(
            "a.usa-button.login-button.login-button--primary.margin-right-2"
        ).text
        == "Sign in with \n"
    )
    assert page.select_one("meta[name=description]") is not None
    # This area is hidden for the pilot
    # assert normalize_spaces(page.select_one('#whos-using-notify').text) == (
    #     'Who’s using Notify.gov '  # Hiding this next area for the pilot
    #     # Hiding this next area for the pilot
    #     # 'See the list of services and organizations. '
    #     'There are 111 Organizations and 9,999 Services using Notify.'
    # )

    assert page.select_one("#whos-using-notify a") is None


def test_logged_in_user_redirects_to_choose_account(
    client_request,
    api_user_active,
    mock_get_user,
    mock_get_user_by_email,
    mock_login,
):
    client_request.get(
        "main.index",
        _expected_status=302,
    )

    # Modify expected URL to include the query parameter
    client_request.get(
        "main.sign_in",
        _expected_status=302,
        _expected_redirect=url_for("main.show_accounts_or_dashboard") + "?next=EMAIL_IS_OK",
    )


def test_robots(client_request):
    client_request.get_url("/robots.txt", _expected_status=404)


@pytest.mark.parametrize(
    "view",
    [
        "privacy",
        "pricing",
        "roadmap",
        "features",
        "documentation",
        "best_practices",
        "clear_goals",
        "rules_and_regulations",
        "establish_trust",
        "write_for_action",
        "multiple_languages",
        "benchmark_performance",
        "security",
        "message_status",
        "features_sms",
        "how_to_pay",
        "get_started",
        "guidance_index",
        "create_and_send_messages",
        "edit_and_format_messages",
        "send_files_by_email",
        "billing_details",
    ],
)
def test_static_pages(client_request, mock_get_organization_by_domain, view, mocker):
    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")

    # Function to check if a view is feature-flagged and should return 404 when disabled
    def is_feature_flagged(view):
        feature_best_practices_enabled = (
            os.getenv("FEATURE_BEST_PRACTICES_ENABLED", "false").lower() == "true"
        )
        feature_flagged_views = [
            "best_practices",
            "clear_goals",
            "rules_and_regulations",
            "establish_trust",
            "write_for_action",
            "multiple_languages",
            "benchmark_performance",
        ]
        return not feature_best_practices_enabled and view in feature_flagged_views

    request = partial(client_request.get, "main.{}".format(view))

    # If the guidance feature is disabled, expect a 404 for feature-flagged views
    if is_feature_flagged(view):
        page = request(_expected_status=404)
    else:
        # Check the page loads when user is signed in
        page = request()
        assert page.select_one("meta[name=description]")

        # Check it still works when they don’t have a recent service
        with client_request.session_transaction() as session:
            session["service_id"] = None
        request()

        # Check it redirects to the login screen when they sign out
        client_request.logout()
        with client_request.session_transaction() as session:
            session["service_id"] = None
            session["user_id"] = None
        request(
            _expected_status=302,
            _expected_redirect="/sign-in?next={}".format(
                url_for("main.{}".format(view))
            ),
        )
