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

    heading = page.h1.text.strip()
    assert heading in [
        "Reach people where they are with government-powered text messages",
        "There's currently a technical issue.",
    ]

    button = page.select_one(
        "a.usa-button.login-button.login-button--primary.margin-right-2"
    )

    if heading == "There's currently a technical issue.":
        assert button is None
    else:
        assert button is not None
        assert "Sign in with" in button.text.strip()
        assert button.find("img")["alt"] == "Login.gov logo"

    assert page.select_one("meta[name=description]") is not None
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
        _expected_redirect=url_for("main.show_accounts_or_dashboard"),
    )


def test_robots(client_request):
    client_request.get_url("/robots.txt", _expected_status=404)


@pytest.mark.parametrize(
    ("endpoint", "kwargs"),
    [
        ("sign_in", {}),
        pytest.param("index", {}, marks=pytest.mark.xfail(raises=AssertionError)),
    ],
)
@freeze_time("2012-12-12 12:12")  # So we don't go out of business hours
def test_hiding_pages_from_search_engines(
    client_request, mock_get_service_and_organization_counts, endpoint, kwargs, mocker
):

    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()
    response = client_request.get_response(f"main.{endpoint}", **kwargs)
    assert "X-Robots-Tag" in response.headers
    assert response.headers["X-Robots-Tag"] == "noindex"

    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert page.select_one("meta[name=robots]")["content"] == "noindex"


@pytest.mark.parametrize(
    "view",
    [
        "privacy",
        "pricing",
        "documentation",
        "best_practices",
        "clear_goals",
        "rules_and_regulations",
        "establish_trust",
        "write_for_action",
        "multiple_languages",
        "benchmark_performance",
        "message_status",
        "how_to_pay",
        "get_started",
        "how_to",
        "create_and_send_messages",
        "edit_and_format_messages",
        "send_files_by_email",
    ],
)
def test_static_pages(client_request, mock_get_organization_by_domain, view, mocker):
    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")

    request = partial(client_request.get, "main.{}".format(view))

    # Assert the page loads successfully
    page = request(_expected_status=200)
    assert page.select_one("meta[name=description]")

    # Check the behavior when no recent service is set
    with client_request.session_transaction() as session:
        session["service_id"] = None
    request()

    # Check redirection to login screen when signed out
    client_request.logout()
    with client_request.session_transaction() as session:
        session["service_id"] = None
        session["user_id"] = None
    request(
        _expected_status=302,
        _expected_redirect="/sign-in?next={}".format(url_for("main.{}".format(view))),
    )


def test_guidance_pages_link_to_service_pages_when_signed_in(client_request, mocker):
    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")

    request = partial(client_request.get, "main.edit_and_format_messages")
    selector = ".list-number li a"

    # Check the page loads when user is signed in
    page = request()
    assert page.select_one(selector)["href"] == url_for(
        "main.choose_template",
        service_id=SERVICE_ONE_ID,
    )

    # Check it still works when they don't have a recent service
    with client_request.session_transaction() as session:
        session["service_id"] = None
    page = request()
    assert not page.select_one(selector)

    # Check it redirects to the login screen when they sign out
    client_request.logout()
    with client_request.session_transaction() as session:
        session["service_id"] = None
        session["user_id"] = None
    request(_expected_status=302)


@pytest.mark.parametrize(
    ("view", "expected_view"),
    [
        ("old_integration_testing", "integration_testing"),
        ("delivery_and_failure", "message_status"),
        ("callbacks", "documentation"),
    ],
)
def test_old_static_pages_redirect(client_request, view, expected_view, mocker):

    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()
    client_request.get(
        "main.{}".format(view),
        _expected_status=301,
        _expected_redirect=url_for(
            "main.{}".format(expected_view),
        ),
    )


def test_css_is_served_from_correct_path(client_request):
    page = client_request.get("main.documentation")  # easy static page

    for index, link in enumerate(page.select("link[rel=stylesheet]")):
        assert link["href"].startswith(
            [
                "https://static.example.com/css/styles.css?",
            ][index]
        )


# Commenting out until after the pilot when we'll decide on a logo
# def test_resources_that_use_asset_path_variable_have_correct_path(client_request):

#     page = client_request.get('main.documentation')  # easy static page

#     logo_svg_fallback = page.select_one('.usa-flag-logo')

#     assert logo_svg_fallback['src'].startswith('https://static.example.com/images/us-notify-color.png')


@pytest.mark.parametrize(
    ("current_date", "expected_rate"),
    [
        ("2022-05-01", "1.72"),
    ],
)
@pytest.mark.skip(reason="Currently hidden for TTS")
def test_sms_price(
    client_request,
    mock_get_service_and_organization_counts,
    current_date,
    expected_rate,
    mocker,
):

    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()

    with freeze_time(current_date):
        home_page = client_request.get("main.index", _test_page_title=False)
        pricing_page = client_request.get("main.pricing")

    assert normalize_spaces(
        home_page.select(".product-page-section")[5].select(".grid-col-6")[1].text
    ) == (
        f"Text messages "
        f"Up to 40,000 free text messages a year, "
        f"then {expected_rate} pence per message"
    )

    assert normalize_spaces(pricing_page.select_one("#text-messages + p + p").text) == (
        f"When a service has used its annual allowance, it costs "
        f"{expected_rate} pence (plus VAT) for each text message you "
        f"send."
    )
