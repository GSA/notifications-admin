# import datetime
import os
import re

from playwright.sync_api import expect

# Env variables should be replaiced by function call.
E2E_TEST_URI = os.getenv("NOTIFY_E2E_TEST_URI")
E2E_TEST_EMAIL = os.getenv("NOTIFY_E2E_TEST_EMAIL")
E2E_TEST_PASS = os.getenv("NOTIFY_E2E_TEST_PASS")


def test_email_revalidation_process(authenticated_page, end_to_end_context):
    page = authenticated_page

    # Start on sign in page
    # page.goto(f"{E2E_TEST_URI}/sign-in")

    # # Check to make sure that we've arrived at the next page.
    # page.wait_for_load_state("domcontentloaded")

    # # Check to make sure that we've arrived at the next page.
    # # Check the page title exists and matches what we expect.
    # # expect(page).to_have_title(re.compile("Sign in – Notify.gov"))

    # # Find the form to submit the email/pass.
    # email_input = page.locator('xpath=//input[@name="email_address"]')
    # password_input = page.locator('xpath=//input[@name="password"]')
    # sign_in_button = page.get_by_role("button", name=re.compile("Continue"))

    # # Cheack that all are visable.
    # expect(email_input).to_be_visible()
    # expect(password_input).to_be_visible()
    # expect(sign_in_button).to_be_visible()

    # # Fill in the form.
    # email_input.fill(" ")
    # password_input.fill(" ")

    # # Click on continue button.
    # sign_in_button.click()

    # # Check to make sure that we've arrived at the next page.
    # page.wait_for_load_state("domcontentloaded")

    # # TODO:  Figure out how to:
    # #        1. Generate a user with email_validated_at > 90 days
    # #        2. Log in to create revalidation process
    # #        2a. Need to handle 2fa automatically
    # #        3. Capture code from the validation email
    # #        4. Verify generated user has email_validated_at = now()
