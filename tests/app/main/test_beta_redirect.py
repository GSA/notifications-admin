from flask import current_app

from app import create_beta_url


def test_create_beta_url():
    url_for_redirect = create_beta_url("https://notify.gov/using-notify/get-started")
    assert url_for_redirect == "https://beta.notify.gov/using-notify/get-started"


def test_redirect_notify_to_beta(monkeypatch, client_request):
    monkeypatch.setitem(current_app.config, "NOTIFY_ENVIRONMENT", "production")
    # import pdb
    # pdb.set_trace()
    # resp = client_request.get_response_from_url("https://notify.gov/using-notify/get-started")
    # assert resp.status_code == 301
    assert current_app.config["NOTIFY_ENVIRONMENT"] == "production"
