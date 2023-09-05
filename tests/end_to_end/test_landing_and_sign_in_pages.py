import os
import re

from playwright.sync_api import expect

from app.utils import skip_auth_for_tests


@skip_auth_for_tests
def test_landing_page(end_to_end_context):
    # Open a new page and go to the staging site.
    page = end_to_end_context.new_page()
    page.goto(os.getenv("NOTIFY_E2E_TEST_URI"))

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    # Check the page title exists and matches what we expect.
    expect(page).to_have_title(re.compile("Notify.gov"))

    # Retrieve some prominent elements on the page for testing.
    main_header = page.get_by_role(
        "heading", name="Send text messages to your participants"
    )
    sign_in_button = page.get_by_role("link", name="Sign in")
    benefits_studio_email = page.get_by_role("link", name="tts-benefits-studio@gsa.gov")

    # Check to make sure the elements are visible.
    expect(main_header).to_be_visible()
    expect(sign_in_button).to_be_visible()
    expect(benefits_studio_email).to_be_visible()

    # Check to make sure the sign-in button and email links are correct.
    expect(sign_in_button).to_have_attribute("href", "/sign-in")
    expect(benefits_studio_email).to_have_attribute(
        "href", "mailto:tts-benefits-studio@gsa.gov"
    )

    # Retrieve all other main content headers and check that they're
    # visible.
    content_headers = [
        "Control your content",
        "See how your messages perform",
        "No technical integration needed",
        "About the product",
    ]

    for content_header in content_headers:
        expect(
            page.get_by_role("heading", name=re.compile(content_header))
        ).to_be_visible()


@skip_auth_for_tests
def test_sign_in_and_mfa_pages(end_to_end_context):
    # Open a new page and go to the staging site.
    page = end_to_end_context.new_page()
    page.goto(os.getenv("NOTIFY_E2E_TEST_URI"))

    sign_in_button = page.get_by_role("link", name="Sign in")

    # Test trying to sign in.
    sign_in_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    # Check the page title exists and matches what we expect.
    expect(page).to_have_title(re.compile("Sign in"))

    # Check for the sign in heading.
    sign_in_heading = page.get_by_role("heading", name="Sign in")
    expect(sign_in_heading).to_be_visible()

    # Check for the sign in form elements.
    # NOTE:  Playwright cannot find input elements by role and recommends using
    #        get_by_label() instead; however, hidden form elements do not have
    #        labels associated with them, hence the XPath!
    # See https://playwright.dev/python/docs/api/class-page#page-get-by-label
    # and https://playwright.dev/python/docs/locators#locate-by-css-or-xpath
    # for more information.
    email_address_input = page.get_by_label("Email address")
    password_input = page.get_by_label("Password")
    csrf_token = page.locator('xpath=//input[@name="csrf_token"]')
    continue_button = page.get_by_role("button", name=re.compile("Continue"))
    forgot_password_link = page.get_by_role("link", name="Forgot your password?")

    # Make sure form elements are visible and not visible as expected.
    expect(email_address_input).to_be_visible()
    expect(password_input).to_be_visible()
    expect(continue_button).to_be_visible()
    expect(forgot_password_link).to_be_visible()

    expect(csrf_token).to_be_hidden()

    # Make sure form elements are configured correctly with the right
    # attributes.
    expect(email_address_input).to_have_attribute("type", "email")
    expect(password_input).to_have_attribute("type", "password")
    expect(csrf_token).to_have_attribute("type", "hidden")
    expect(continue_button).to_have_attribute("type", "submit")
    expect(forgot_password_link).to_have_attribute("href", "/forgot-password")

    # Sign in to the site.
    email_address_input.fill(os.getenv("NOTIFY_E2E_TEST_EMAIL"))
    password_input.fill(os.getenv("NOTIFY_E2E_TEST_PASSWORD"))
    continue_button.click()

    # Wait for the next page to fully load.
    page.wait_for_load_state("domcontentloaded")

    # Check the page title exists and matches what we expect.
    expect(page).to_have_title(re.compile("Check your phone"))

    # Check for the sign in heading.
    sign_in_heading = page.get_by_role("heading", name="Check your phone")
    expect(sign_in_heading).to_be_visible()

    # Check for the sign in form elements.
    # NOTE:  Playwright cannot find input elements by role and recommends using
    #        get_by_label() instead; however, hidden form elements do not have
    #        labels associated with them, hence the XPath!
    # See https://playwright.dev/python/docs/api/class-page#page-get-by-label
    # and https://playwright.dev/python/docs/locators#locate-by-css-or-xpath
    # for more information.
    mfa_input = page.get_by_label("Text message code")
    csrf_token = page.locator('xpath=//input[@name="csrf_token"]')
    continue_button = page.get_by_role("button", name=re.compile("Continue"))
    not_received_message_link = page.get_by_role(
        "link", name="Not received a text message?"
    )

    # Make sure form elements are visible and not visible as expected.
    expect(mfa_input).to_be_visible()
    expect(continue_button).to_be_visible()
    expect(not_received_message_link).to_be_visible()

    expect(csrf_token).to_be_hidden()

    # Make sure form elements are configured correctly with the right
    # attributes.
    expect(mfa_input).to_have_attribute("type", "tel")
    expect(mfa_input).to_have_attribute("pattern", "[0-9]*")
    expect(csrf_token).to_have_attribute("type", "hidden")
    expect(continue_button).to_have_attribute("type", "submit")
    expect(not_received_message_link).to_have_attribute("href", "/text-not-received")

    # Enter MFA code and continue.
    # TODO: Revisit this at a later point in time.
    # totp = pyotp.TOTP(
    #     os.getenv('MFA_TOTP_SECRET'),
    #     digits=int(os.getenv('MFA_TOTP_LENGTH'))
    # )

    # mfa_input.fill('totp.now()')
    # continue_button.click()

    # # Check to make sure that we've arrived at the next page.
    # page.wait_for_load_state('domcontentloaded')

    # # Check that no MFA code error happened.
    # code_not_found_error = page.get_by_text('Code not found')
    # expect(code_not_found_error).to_have_count(0)

    # # Check the page title exists and matches what we expect.
    # # This could be either the Dashboard of a service if there is only
    # # one, or choosing a service if there are multiple.
    # expect(page).to_have_title(re.compile('Dashboard|Choose service'))
