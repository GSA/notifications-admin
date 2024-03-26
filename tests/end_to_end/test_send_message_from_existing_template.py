import datetime
import os
import re
import uuid

from playwright.sync_api import expect

E2E_TEST_URI = os.getenv("NOTIFY_E2E_TEST_URI")


def _setup(page, end_to_end_context):
    # Prepare for adding a new service later in the test.
    current_date_time = datetime.datetime.now()
    new_service_name = "E2E Federal Test Service {now} - {browser_type}".format(
        now=current_date_time.strftime("%m/%d/%Y %H:%M:%S"),
        browser_type=end_to_end_context.browser.browser_type.name,
    )

    page.goto(f"{E2E_TEST_URI}/accounts")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    # Check to make sure that we've arrived at the next page.
    # Check the page title exists and matches what we expect.
    expect(page).to_have_title(re.compile("Choose service"))

    # Check for the sign in heading.
    sign_in_heading = page.get_by_role("heading", name="Choose service")
    expect(sign_in_heading).to_be_visible()

    # Retrieve some prominent elements on the page for testing.
    add_service_button = page.get_by_role(
        "button", name=re.compile("Add a new service")
    )

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

    # Check for the service name title and heading.
    service_heading = page.get_by_text(new_service_name, exact=True)

    expect(service_heading).to_be_visible()
    expect(page).to_have_title(re.compile(new_service_name))

    return new_service_name


def handle_no_existing_template_case(page):
    print(f"ENTER HANDLE_NO_EXISTING_TEMPLATE_CASE")
    print(page.content())
    create_template_button = page.get_by_text("Create your first template")
    expect(create_template_button).to_be_visible()
    create_template_button.click()
    print("GOT TO CREATE TEMPLATE")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    new_template_button = page.get_by_text("New template")
    expect(new_template_button).to_be_visible()
    new_template_button.click()
    print("GOT TO NEW TEMPLATE")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    start_with_a_blank_template_radio = page.get_by_text("Start with a blank template")
    expect(start_with_a_blank_template_radio).to_be_visible()
    start_with_a_blank_template_radio.click()
    print("GOT TO START WITH A BLANK TEMPLATE")

    continue_button = page.get_by_role("button", name="Continue")

    # continue_button = page.get_by_text("Continue")
    expect(continue_button).to_be_visible()
    continue_button.click()
    print("GOT TO CONTINUE")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    template_name_input = page.get_by_text("Template name")
    expect(template_name_input).to_be_visible()
    template_name = str(uuid.uuid4())
    template_name_input.fill(template_name)
    print("GOT TEMPLATE NAME INPUT")
    message_input = page.get_by_role("textbox", name="Message")
    expect(message_input).to_be_visible()
    message = "Test message"
    message_input.fill(message)
    print("FILLED OUT NEW TEMPLATE")

    save_button = page.get_by_text("Save")
    expect(save_button).to_be_visible()
    save_button.click()
    print("SAVED NEW TEMPLATE")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    use_this_template_button = page.get_by_text("Use this template")
    expect(use_this_template_button).to_be_visible()
    use_this_template_button.click()
    print("DID USE THIS TEMPLATE")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    use_my_phone_number_link = page.get_by_text("Use my phone number")
    expect(use_my_phone_number_link).to_be_visible()
    use_my_phone_number_link.click()
    print("DID USE MY PHONE NUBMER")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    preview_button = page.get_by_text("Preview")
    expect(preview_button).to_be_visible()
    preview_button.click()
    print("DID PREVIEW")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    send_button = page.get_by_role("button", name="Send")
    expect(send_button).to_be_visible()
    send_button.click()
    print("DID SEND")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    print(f"PAGE!!! {page.content()}")

    dashboard_button = page.get_by_role("button", name="Dashboard")
    expect(dashboard_button).to_be_visible()
    dashboard_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    download_link = page.get_by_text("Download")
    expect(download_link).to_be_visible()

    # Start waiting for the download
    with page.expect_download() as download_info:
        # Perform the action that initiates download
        download_link.click()
    download = download_info.value
    # Wait for the download process to complete and save the downloaded file somewhere
    download.save_as("download_test_file")
    f = open("download_test_file", "r")

    content = f.read()
    f.close()
    # We don't want to wait 5 minutes to get a response from AWS about the message we sent
    # So we are using this invalid phone number the e2e_test_user signed up with (12025555555)
    # to shortcircuit the sending process.  Our phone number validator will insta-fail the
    # message and it won't be sent, but the report will still be generated, which is all
    # we care about here.
    assert (
        "Phone Number,Template,Sent by,Batch File,Carrier Response,Status,Time"
        in content
    )
    assert "12025555555" in content
    assert "one-off-e2e_test_user" in content
    os.remove("download_test_file")


def handle_existing_template_case(page):
    existing_template_link = page.get_by_text("Example text message template")
    expect(existing_template_link).to_be_visible()
    existing_template_link.click()
    print("GOT TO EXISTING TEMPLATE")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    print(page.content())

    use_this_template_button = page.get_by_text("Use this template")
    expect(use_this_template_button).to_be_visible()
    use_this_template_button.click()
    print("GOT TO USE THIS TEMPLATE")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    use_my_phone_number_link = page.get_by_text("Use my phone number")
    expect(use_my_phone_number_link).to_be_visible()
    use_my_phone_number_link.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    day_of_week_input = page.get_by_text("day of week")
    expect(day_of_week_input).to_be_visible()
    day_of_week_input.fill("Monday")
    print("GOT DAY OF WEEK INPUT")

    continue_button = page.get_by_role("button", name="Continue")

    # continue_button = page.get_by_text("Continue")
    expect(continue_button).to_be_visible()
    continue_button.click()
    print("GOT TO CONTINUE")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    color_input = page.get_by_text("color")
    expect(day_of_week_input).to_be_visible()
    day_of_week_input.fill("Green")
    print("GOT COLOR INPUT")

    continue_button = page.get_by_role("button", name="Continue")

    # continue_button = page.get_by_text("Continue")
    expect(continue_button).to_be_visible()
    continue_button.click()
    print("GOT TO CONTINUE")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    preview_button = page.get_by_text("Preview")
    expect(preview_button).to_be_visible()
    preview_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    send_button = page.get_by_role("button", name="Send")
    expect(send_button).to_be_visible()
    send_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    dashboard_button = page.get_by_text("Dashboard")
    expect(dashboard_button).to_be_visible()
    dashboard_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    download_link = page.get_by_text("Download")
    expect(download_link).to_be_visible()

    # Start waiting for the download
    with page.expect_download() as download_info:
        # Perform the action that initiates download
        download_link.click()
    download = download_info.value
    # Wait for the download process to complete and save the downloaded file somewhere
    download.save_as("download_test_file")
    f = open("download_test_file", "r")

    content = f.read()
    f.close()
    # We don't want to wait 5 minutes to get a response from AWS about the message we sent
    # So we are using this invalid phone number the e2e_test_user signed up with (12025555555)
    # to shortcircuit the sending process.  Our phone number validator will insta-fail the
    # message and it won't be sent, but the report will still be generated, which is all
    # we care about here.
    assert (
        "Phone Number,Template,Sent by,Batch File,Carrier Response,Status,Time"
        in content
    )
    assert "12025555555" in content
    assert "one-off-e2e_test_user" in content
    os.remove("download_test_file")


def test_send_message_from_existing_template(authenticated_page, end_to_end_context):
    page = authenticated_page
    print(f"START OF TEST")


    new_service_name = _setup(page, end_to_end_context)
    #print(page.content())

    # if page.get_by_text("Create your first template"):
    #    handle_no_existing_template_case(page)
    #else:
    handle_existing_template_case(page)

    _teardown(page)


def _teardown(page):
    page.click("text='Settings'")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    page.click("text='Delete this service'")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    page.click("text='Yes, delete'")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    # Check to make sure that we've arrived at the next page.
    # Check the page title exists and matches what we expect.
    expect(page).to_have_title(re.compile("Choose service"))
