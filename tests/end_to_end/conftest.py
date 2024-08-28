import os
import re

import pytest

E2E_TEST_URI = os.getenv("NOTIFY_E2E_TEST_URI")


def login_for_end_to_end_testing(browser):
    # Open a new page and go to the staging site.
    context = browser.new_context()
    page = context.new_page()
    page.goto(f"{E2E_TEST_URI}/sign-in")

    #sign_in_button = page.get_by_role("link", name="Sign in")

    # Test trying to sign in.
    #sign_in_button.click()

    # Wait for the next page to fully load.
    page.wait_for_load_state("domcontentloaded")
    print(f"PAGE ON CONFTEST AFTER SIGNIN IS {page}")
    # Save storage state into the file.
    auth_state_path = os.path.join(
        os.getenv("NOTIFY_E2E_AUTH_STATE_PATH"), "state.json"
    )
    context.storage_state(path=auth_state_path)


@pytest.fixture
def end_to_end_authenticated_context(browser):
    # Create and load a previously authenticated context for Playwright E2E
    # tests.
    # login_for_end_to_end_testing(browser)

    auth_state_path = os.path.join(
        os.getenv("NOTIFY_E2E_AUTH_STATE_PATH"), "state.json"
    )

    context = browser.new_context(storage_state=auth_state_path)

    return context


@pytest.fixture
def end_to_end_context(browser):
    context = browser.new_context()
    return context


def pytest_generate_tests(metafunc):
    os.environ["DANGEROUS_SALT"] = os.getenv("E2E_DANGEROUS_SALT")
    os.environ["SECRET_KEY"] = os.getenv("E2E_SECRET_KEY")
    os.environ["ADMIN_CLIENT_SECRET"] = os.getenv("E2E_ADMIN_CLIENT_SECRET")
    os.environ["ADMIN_CLIENT_USERNAME"] = os.getenv("E2E_ADMIN_CLIENT_USERNAME")
    os.environ["NOTIFY_ENVIRONMENT"] = os.getenv("E2E_NOTIFY_ENVIRONMENT")
    os.environ["API_HOST_NAME"] = os.getenv("E2E_API_HOST_NAME")


@pytest.fixture
def authenticated_page(end_to_end_context):
    # Open a new page and go to the site.
    page = end_to_end_context.new_page()
    page.goto(f"{E2E_TEST_URI}/sign-in")


    # Wait for the next page to fully load.
    page.wait_for_load_state("domcontentloaded")

    return page
