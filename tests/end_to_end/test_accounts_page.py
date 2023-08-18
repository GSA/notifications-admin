import os
import re

from playwright.sync_api import expect


def test_accounts_page(end_to_end_authenticated_context):
    # Open a new page and go to the staging site.
    page = end_to_end_authenticated_context.new_page()

    accounts_uri = '{}accounts'.format(os.getenv('NOTIFY_E2E_TEST_URI'))

    page.goto(accounts_uri)

    # Check to make sure that we've arrived at the next page.
    # Check the page title exists and matches what we expect.
    expect(page).to_have_title(re.compile('Choose service'))

    # Check for the sign in heading.
    sign_in_heading = page.get_by_role('heading', name='Choose service')
    expect(sign_in_heading).to_be_visible()

    # Retrieve some prominent elements on the page for testing.
    add_service_button = page.get_by_role(
        'button',
        name=re.compile('Add a new service')
    )

    expect(add_service_button).to_be_visible()
