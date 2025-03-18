import os
import re

from playwright.sync_api import expect

from tests.end_to_end.conftest import check_axe_report

E2E_TEST_URI = os.getenv("NOTIFY_E2E_TEST_URI")


def test_landing_page(end_to_end_context):
    # Open a new page and go to the site.
    page = end_to_end_context.browser.new_page()
    page.goto(f"{E2E_TEST_URI}/")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    # Check the page title exists and matches what we expect.
    expect(page).to_have_title(re.compile("Notify.gov"))

    # Retrieve some prominent elements on the page for testing.
    main_header = page.get_by_role(
        "heading",
        name="Reach people where they are with government-powered text messages",
    )
    sign_in_button = page.get_by_role("link", name="Sign in with")

    # Check to make sure the elements are visible.
    expect(main_header).to_be_visible()
    expect(sign_in_button).to_be_visible()

    # Check to make sure the sign-in button and email links are correct.
    href_value = sign_in_button.get_attribute("href")
    assert href_value is not None, "The sign-in button does not have an href attribute"

    # Retrieve all other main content headers and check that they're
    # visible.
    content_headers = [
        "Government texting made easy",
        "Key features",
    ]

    for content_header in content_headers:
        expect(
            page.get_by_role("heading", name=re.compile(content_header))
        ).to_be_visible()
