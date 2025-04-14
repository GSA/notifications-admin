import datetime
import os
from contextlib import contextmanager
from unittest.mock import patch

import pytest
from axe_core_python.sync_playwright import Axe
from flask import Flask, current_app, url_for
from flask import session as flask_session
from flask_login import login_user
from flask.testing import FlaskClient

from app import create_app
from app.models.user import User
from app.notify_client.service_api_client import service_api_client
from app.notify_client.user_api_client import user_api_client
from .. import TestClient


E2E_TEST_URI = os.getenv("NOTIFY_E2E_TEST_URI")

class TestClient(FlaskClient):
    def login(self, user, mocker=None, service=None):
        # Skipping authentication here and just log them in
        model_user = User(user)
        with self.session_transaction() as session:
            session["current_session_id"] = model_user.current_session_id
            session["user_id"] = model_user.id
        if mocker:
            mocker.patch("app.user_api_client.get_user", return_value=user)
        if mocker and service:
            with self.session_transaction() as session:
                session["service_id"] = service["id"]
            mocker.patch(
                "app.service_api_client.get_service", return_value={"data": service}
            )

        with patch("app.events_api_client.create_event"):
            login_user(model_user, force=True)  # forces the user to be logged in.
        with self.session_transaction() as test_session:
            for key, value in flask_session.items():
                test_session[key] = value

    def logout(self, user):
        self.get(url_for("main.sign_out"))


@pytest.fixture
def end_to_end_context(browser):
    context = browser.new_context()
    return context


@pytest.fixture
def authenticated_page(end_to_end_context):
    # Open a new page and go to the site.
    page = end_to_end_context.new_page()
    page.goto(f"{E2E_TEST_URI}/sign-in")

    # Wait for the next page to fully load.
    page.wait_for_load_state("domcontentloaded")

    return page


def check_axe_report(page):
    axe = Axe()

    results = axe.run(page)

    # TODO fix remaining 'moderate' failures
    # so we can set the level we skip to minor only
    for violation in results["violations"]:
        assert violation["impact"] in [
            "minor",
            "moderate",
        ], f"Accessibility violation: {violation}"


@pytest.fixture
def notify_admin_e2e():
    os.environ["NOTIFY_ENVIRONMENT"] = "e2etest"

    application = Flask("app")
    create_app(application)

    application.test_client_class = TestClient

    with application.app_context():
        yield application


@pytest.fixture
def default_user(notify_admin_e2e):
    user_data = user_api_client.get_user_by_email(os.getenv("NOTIFY_E2E_TEST_EMAIL"))
    return user_data


@pytest.fixture
def client(notify_admin_e2e, default_user):
    """
    Do not use this fixture directly – use `client_request` instead
    """
    with notify_admin_e2e.test_request_context(), notify_admin_e2e.test_client() as client:
        client.allow_subdomain_redirects = True
        try:
            client.login(default_user)
            yield client
        finally:
            client.logout(default_user)


# Need e2e service defined here?
@pytest.fixture
def default_service(browser, client, default_user):
    current_date_time = datetime.datetime.now()
    now = current_date_time.strftime("%m/%d/%Y %H:%M:%S")
    browser_type = browser.browser_type.name
    service_name = f"E2E Federal Test Service {now} - {browser_type}"

    service = service_api_client.create_service(
        service_name,
        "federal",
        current_app.config["DEFAULT_SERVICE_LIMIT"],
        True,
        default_user["id"],
        default_user["email_address"],
    )

    print("OK I GOT HERE LETS GO!!!")

    yield service

    service_api_client.archive_service(service.id, None)


@contextmanager
def _set_up_user(
    default_service,
    name,
    email_addr,
    phone,
    password,
    auth_type,
    permissions,
    folder_permissions,
):
    user = user_api_client.get_user_by_email_or_none(email_addr)
    if user is None:
        user = user_api_client.register_user(
            name, email_addr, phone, password, auth_type
        )
    user_api_client.add_user_to_service(
        default_service.id, user.id, permissions, folder_permissions
    )
    user_api_client.activate_user(user.id)
    yield user
    user_api_client.deactivate_user(user.id)
    service_api_client.remove_user_from_service(user.id, default_service.id)


@pytest.fixture
def admin_user(default_service):
    with _set_up_user(
        default_service,
        "E2E Admin Test",
        "admin@nowhere.huh",
        "1234567890",
        "password",
        "sms",
    ) as user:
        yield user
