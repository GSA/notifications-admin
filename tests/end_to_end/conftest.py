import os

import pytest
from axe_core_python.sync_playwright import Axe

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
        ], f"Accessibility violation: {violation}"
