import os
from functools import partial

import pytest
from flask import url_for


@pytest.mark.parametrize(
    "view",
    [
        "privacy",
        "pricing",
        "roadmap",
        "features",
        "documentation",
        "guidance",
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
        feature_guidance_enabled = (
            os.getenv("FEATURE_GUIDANCE_ENABLED", "false").lower() == "true"
        )
        feature_flagged_views = [
            "guidance",
            "clear_goals",
            "rules_and_regulations",
            "establish_trust",
            "write_for_action",
            "multiple_languages",
            "benchmark_performance",
        ]
        return not feature_guidance_enabled and view in feature_flagged_views

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
