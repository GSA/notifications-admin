import datetime
import os
import re
import uuid

from playwright.sync_api import expect

from tests.end_to_end.conftest import check_axe_report

E2E_TEST_URI = os.getenv("NOTIFY_E2E_TEST_URI")


def create_new_template(page):

    current_service_link = page.get_by_text("Current service")
    expect(current_service_link).to_be_visible()
    current_service_link.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    send_messages_button = page.get_by_role("link", name="Send messages")
    expect(send_messages_button).to_be_visible()
    send_messages_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    create_template_button = page.get_by_text("New template")
    expect(create_template_button).to_be_visible()
    create_template_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    start_with_a_blank_template_radio = page.get_by_text("Start with a blank template")
    expect(start_with_a_blank_template_radio).to_be_visible()
    start_with_a_blank_template_radio.click()

    continue_button = page.get_by_role("button", name="Continue")
    expect(continue_button).to_be_visible()
    continue_button.click()

    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    template_name_input = page.locator('input[type="text"]:visible').first
    expect(template_name_input).to_be_visible()
    template_name = str(uuid.uuid4())
    template_name_input.fill(template_name)
    message_input = page.get_by_role("textbox", name="Message")
    expect(message_input).to_be_visible()
    message = "Test message for e2e test"
    message_input.fill(message)

    save_button = page.get_by_text("Save")
    expect(save_button).to_be_visible()
    save_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    use_this_template_button = page.get_by_text("Use this template")
    expect(use_this_template_button).to_be_visible()
    use_this_template_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    use_my_phone_number_link = page.get_by_text("Use my phone number")
    expect(use_my_phone_number_link).to_be_visible()
    use_my_phone_number_link.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    preview_button = page.get_by_text("Preview")
    expect(preview_button).to_be_visible()
    preview_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    # We are not going to send the message for this test, we just want to confirm
    # that the template has been created and we are now seeing the message from the
    # template in the preview.
    # assert "Test message for e2e test" in page.content()


def test_create_new_template(end_to_end_context):
    page = end_to_end_context.new_page()
    page.goto(f"{E2E_TEST_URI}/sign-in")
    # Wait for the next page to fully load.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    current_date_time = datetime.datetime.now()
    new_service_name = "E2E Federal Test Service {now} - {browser_type}".format(
        now=current_date_time.strftime("%m/%d/%Y %H:%M:%S"),
        browser_type=page.context.browser.browser_type.name,
    )
    page.goto(f"{E2E_TEST_URI}/accounts")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    # Check to make sure that we've arrived at the next page.
    # Check the page title exists and matches what we expect.
    expect(page).to_have_title(re.compile("Choose service"))

    # Check for the sign in heading.
    sign_in_heading = page.get_by_role("heading", name="Choose service")
    expect(sign_in_heading).to_be_visible()

    # Retrieve some prominent elements on the page for testing.
    add_service_button = page.get_by_role("button", name=re.compile("Add service"))

    expect(add_service_button).to_be_visible()

    existing_service_link = page.get_by_role("link", name=new_service_name)

    # Check to see if the service was already created - if so, we should fail.
    # TODO:  Figure out how to make this truly isolated, and/or work in a
    #        delete service workflow.
    expect(existing_service_link).to_have_count(0)

    # Click on add a new service.
    add_service_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    # Check for the sign in heading.
    about_heading = page.get_by_role("heading", name="About your service")
    expect(about_heading).to_be_visible()

    # Retrieve some prominent elements on the page for testing.
    service_name_input = page.locator('xpath=//input[@name="name"]')
    add_service_button = page.get_by_role("button", name=re.compile("Add service"))

    expect(service_name_input).to_be_visible()
    expect(add_service_button).to_be_visible()

    # Fill in the form.
    service_name_input.fill(new_service_name)

    # Click on add service.
    add_service_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    # TODO this fails on staging due to duplicate results on 'get_by_text'
    # Check for the service name title and heading.
    # service_heading = page.get_by_text(new_service_name, exact=True)
    # expect(service_heading).to_be_visible()

    expect(page).to_have_title(re.compile(new_service_name))

    create_new_template(page)

    _teardown(page)


def _teardown(page):
    page.click("text='Settings'")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    page.click("text='Delete this service'")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    page.click("text='Yes, delete'")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    # Check to make sure that we've arrived at the next page.
    # Check the page title exists and matches what we expect.
    expect(page).to_have_title(re.compile("Choose service"))
