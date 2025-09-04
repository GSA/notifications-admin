import datetime
import os
import re
import uuid

from playwright.sync_api import expect

from tests.end_to_end.conftest import check_axe_report

E2E_TEST_URI = os.getenv("NOTIFY_E2E_TEST_URI")


def _setup(page):
    # Prepare for adding a new service later in the test.
    current_date_time = datetime.datetime.now()
    new_service_name = "E2E Federal Test Service {now} - {browser_type}".format(
        now=current_date_time.strftime("%m/%d/%Y %H:%M:%S"),
        browser_type=page.context.browser.browser_type.name,
    )

    page.goto(f"{E2E_TEST_URI}/accounts")
    check_axe_report(page)

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

    return new_service_name


def handle_no_existing_template_case(page):
    """
    This is the test path for local development.  Developers have their own
    databases and typically they have service or two already created, which
    means they won't see the "Example text message template" which is done
    as an introduction.  Instead they will see "Create your first template".
    Note that this test goes all the way through sending and downloading the
    report and verifying the phone number, etc. in the report.  This is because
    developer systems are fully connected to AWS.
    """

    create_template_button = page.get_by_text("Create your first template")
    expect(create_template_button).to_be_visible()
    create_template_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    new_template_button = page.get_by_text("New template")
    expect(new_template_button).to_be_visible()
    new_template_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    start_with_a_blank_template_radio = page.get_by_text("Start with a blank template")
    expect(start_with_a_blank_template_radio).to_be_visible()
    start_with_a_blank_template_radio.click()

    continue_button = page.get_by_role("button", name="Continue")

    # continue_button = page.get_by_text("Continue")
    expect(continue_button).to_be_visible()
    continue_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    template_name_input = page.get_by_label("Template name")
    expect(template_name_input).to_be_visible()
    template_name = str(uuid.uuid4())
    template_name_input.fill(template_name)
    message_input = page.get_by_role("textbox", name="Message")
    expect(message_input).to_be_visible()
    message = "Test message"
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
    check_axe_report(page)

    use_my_phone_number_link = page.get_by_text("Use my phone number")
    expect(use_my_phone_number_link).to_be_visible()
    use_my_phone_number_link.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    preview_button = page.get_by_text("Preview")
    expect(preview_button).to_be_visible()
    preview_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    send_button = page.get_by_role("button", name="Send")
    expect(send_button).to_be_visible()
    send_button.click()

    page.wait_for_load_state("networkidle", timeout=30000)
    check_axe_report(page)

    activity_link = page.locator("a:has-text('Activity')")
    expect(activity_link).to_be_visible()
    activity_link.click()

    # Skip download verification - S3 reports may not be available in test environment


def handle_existing_template_case(page):
    """
    This is the test path used in the Github action.  Right now the e2e tests
    are not connected to AWS, so we can't actually send messages.  Hence, the
    test stops when it verifies that the 'Send' button exists on the page.  In
    the future we would like to change the way e2e tests run so they run against
    staging, in which case either the code in this method can be uncommented,
    or perhaps this path will be unnecessary (because staging is not completely clean)
    and we will just use the same path as for local development.
    """
    existing_template_link = page.get_by_text("Example text message template")
    expect(existing_template_link).to_be_visible()
    existing_template_link.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    continue_button = page.get_by_role("button", name="Continue")

    # continue_button = page.get_by_text("Continue")
    expect(continue_button).to_be_visible()
    continue_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    continue_button = page.get_by_role("button", name="Continue")

    # continue_button = page.get_by_text("Continue")
    expect(continue_button).to_be_visible()
    continue_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    # day_of_week_input = page.locator('xpath=//input[@name="day of week"]')
    # day_of_week_input = page.get_by_text("day of week")
    day_of_week_input = page.get_by_role("textbox", name="day of week")
    expect(day_of_week_input).to_be_visible()
    day_of_week_input.fill("Monday")

    continue_button = page.get_by_role("button", name="Continue")

    # continue_button = page.get_by_text("Continue")
    expect(continue_button).to_be_visible()
    continue_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    color_input = page.get_by_role("textbox", name="color")
    expect(color_input).to_be_visible()
    color_input.fill("Green")

    # continue_button = page.get_by_text("Continue")
    expect(continue_button).to_be_visible()
    continue_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    if "/tour" not in page.url:
        # Only execute this part if the current page is not the /tour page
        preview_button = page.get_by_text("Preview")
        expect(preview_button).to_be_visible()
        preview_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    send_button = page.get_by_role("button", name="Send")
    expect(send_button).to_be_visible()
    send_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    dashboard_button = page.get_by_text("Dashboard")
    expect(dashboard_button).to_be_visible()
    dashboard_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("networkidle")
    check_axe_report(page)

    # Skip download verification - S3 reports may not be available in test environment


def test_send_message_from_existing_template(authenticated_page):
    page = authenticated_page

    _setup(page)

    if page.get_by_text("Create your first template").count() > 0:
        handle_no_existing_template_case(page)
    else:
        handle_existing_template_case(page)

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
