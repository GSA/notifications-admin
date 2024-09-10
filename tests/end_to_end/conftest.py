import os

import pytest

E2E_TEST_URI = os.getenv("NOTIFY_E2E_TEST_URI")


def login_for_end_to_end_testing(browser):
    # Open a new page and go to the staging site.
    context = browser.new_context()
    page = context.new_page()
    page.goto(f"{E2E_TEST_URI}/sign-in")

    # Wait for the next page to fully load.
    page.wait_for_load_state("domcontentloaded")
    # Save storage state into the file.
    auth_state_path = os.path.join(
        os.getenv("NOTIFY_E2E_AUTH_STATE_PATH"), "state.json"
    )
    context.storage_state(path=auth_state_path)


@pytest.fixture
def end_to_end_authenticated_context(browser):

    auth_state_path = os.path.join(
        os.getenv("NOTIFY_E2E_AUTH_STATE_PATH"), "state.json"
    )

    context = browser.new_context(storage_state=auth_state_path)

    return context


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
