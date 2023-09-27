from flask import current_app

from app import create_beta_url


def test_create_beta_url():
    url_for_redirect = create_beta_url("https://notify.gov/using-notify/get-started")
    assert url_for_redirect == "https://beta.notify.gov/using-notify/get-started"


def test_no_redirect_notify_to_beta_non_production(monkeypatch, client_request):
    monkeypatch.setitem(current_app.config, "NOTIFY_ENVIRONMENT", "development")
    assert current_app.config["NOTIFY_ENVIRONMENT"] == "development"

    client_request.get_response_from_url(
        "https://notify.gov/using-notify/get-started", _expected_status=200
    )


def test_redirect_notify_to_beta(monkeypatch, client_request):
    monkeypatch.setitem(current_app.config, "NOTIFY_ENVIRONMENT", "production")
    assert current_app.config["NOTIFY_ENVIRONMENT"] == "production"

    client_request.get_response_from_url(
        "https://notify.gov/using-notify/get-started", _expected_status=302
    )


def test_no_redirect_beta_notify_to_beta(monkeypatch, client_request):
    monkeypatch.setitem(current_app.config, "NOTIFY_ENVIRONMENT", "production")
    assert current_app.config["NOTIFY_ENVIRONMENT"] == "production"

    client_request.get_response_from_url(
        "https://beta.notify.gov/using-notify/get-started", _expected_status=200
    )
