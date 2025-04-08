import datetime
import os
from contextlib import contextmanager

import pytest
from axe_core_python.sync_playwright import Axe
from flask import Flask, current_app

from app import create_app
from app.notify_client.service_api_client import service_api_client
from app.notify_client.user_api_client import user_api_client

from .. import TestClient

E2E_TEST_URI = os.getenv("NOTIFY_E2E_TEST_URI")


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
    default_user = user_api_client.get_user_by_email(os.getenv("NOTIFY_E2E_TEST_EMAIL"))
    return default_user


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

    from pprint import pprint

    pprint(default_user)
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
