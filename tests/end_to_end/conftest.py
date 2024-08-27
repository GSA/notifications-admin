import os
import re

import pytest

E2E_TEST_URI = os.getenv("NOTIFY_E2E_TEST_URI")


def login_for_end_to_end_testing(browser):
    # Open a new page and go to the staging site.
    print("LOGIN FOR E2E TESTING!")
    context = browser.new_context()
    page = context.new_page()
    page.goto(f"{E2E_TEST_URI}/")
    print("WENT TO SIGNIN PAGE")
    sign_in_button = page.get_by_role("link", name="Sign in")
    print(f"GOT SIGN IN BUTTON? {sign_in_button}")
    # Test trying to sign in.
    sign_in_button.click()
    print("CLICKED SIGNIN BUTTON")
    # Wait for the next page to fully load.
    page.wait_for_load_state("domcontentloaded")
    print("WAITED FOR LOAD STATE")
    # Check for the sign in form elements.
    # NOTE:  Playwright cannot find input elements by role and recommends using
    #        get_by_label() instead; however, hidden form elements do not have
    #        labels associated with them, hence the XPath!
    # See https://playwright.dev/python/docs/api/class-page#page-get-by-label
    # and https://playwright.dev/python/docs/locators#locate-by-css-or-xpath
    # for more information.
    email_address_input = page.get_by_label("Email address")
    print("GOT THE EMAIL INPUT BOX")
    password_input = page.get_by_label("Password")
    print("GOT THE PASSWORD INPUT BOX")
    continue_button = page.get_by_role("button", name=re.compile("Continue"))
    print("GOT THE CONTINUE BUTTON")

    # Sign in to the site.
    email_address_input.fill(os.getenv("NOTIFY_E2E_TEST_EMAIL"))
    print("FILLED THE EMAIL INPUT BOX")
    password_input.fill(os.getenv("NOTIFY_E2E_TEST_PASSWORD"))
    print("FILLED THE PASSWORD INPUT BOX")
    continue_button.click()
    print("CLICKED THE CONTINUE BUTTON")
    # Wait for the next page to fully load.
    page.wait_for_load_state("domcontentloaded")
    print("WAITED FOR PAGE TO LOAD")
    # Check for the sign in form elements.
    # NOTE:  Playwright cannot find input elements by role and recommends using
    #        get_by_label() instead; however, hidden form elements do not have
    #        labels associated with them, hence the XPath!
    # See https://playwright.dev/python/docs/api/class-page#page-get-by-label
    # and https://playwright.dev/python/docs/locators#locate-by-css-or-xpath
    # for more information.
    # mfa_input = page.get_by_label('Text message code')
    # continue_button = page.get_by_role('button', name=re.compile('Continue'))

    # # Enter MFA code and continue.
    # TODO: Revisit this at a later point in time.
    # totp = pyotp.TOTP(
    #     os.getenv('MFA_TOTP_SECRET'),
    #     digits=int(os.getenv('MFA_TOTP_LENGTH'))
    # )

    # mfa_input.fill(totp.now())
    # continue_button.click()

    # page.wait_for_load_state('domcontentloaded')

    # Save storage state into the file.
    auth_state_path = os.path.join(
        os.getenv("NOTIFY_E2E_AUTH_STATE_PATH"), "state.json"
    )
    context.storage_state(path=auth_state_path)
    print("EVERYTHING SHOULD BE GOOD")


@pytest.fixture
def end_to_end_authenticated_context(browser):
    # Create and load a previously authenticated context for Playwright E2E
    # tests.
    # login_for_end_to_end_testing(browser)

    auth_state_path = os.path.join(
        os.getenv("NOTIFY_E2E_AUTH_STATE_PATH"), "state.json"
    )
    context = browser.new_context(storage_state=auth_state_path)
    print(f"RETURNING THE AUTHENTICATED CONTEXT {context}")
    return context


@pytest.fixture
def end_to_end_context(browser):
    context = browser.new_context()
    return context


@pytest.fixture
def authenticated_page(end_to_end_context):
    # Open a new page and go to the site.
    print("ENTER AUTHENTICATED PAGE")
    page = end_to_end_context.new_page()
    page.goto(f"{E2E_TEST_URI}/")
    print("WE WENT TO THE E2E TEST URI")

    # Wait for the next page to fully load.
    page.wait_for_load_state("domcontentloaded")
    print("WE WAITED FOR THE PAGE TO LOAD")
    # Sign in to the site - E2E test accounts are set to flow through.
    sign_in_button = page.get_by_role("link", name="Sign in")
    print("WE FOUND THE SIGNIN BUTTON?")
    sign_in_button.click()
    print("WE CLICKED THE SIGN IN BUTTON")

    # Wait for the next page to fully load.
    page.wait_for_load_state("domcontentloaded")
    print("WE WAITED FOR LOAD STATE AND WE ARE ALL GOOD NOW")
    print(page)

    return page
