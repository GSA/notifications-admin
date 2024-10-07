import datetime
import os
import re

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


def test_invite_team_member_to_service(authenticated_page):
    page = authenticated_page

    _setup(page)

    page.click("text='Settings'")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    # Check to make sure team members link is on left nav.
    team_members_link = page.get_by_text("Team members")
    expect(team_members_link).to_be_visible()
    team_members_link.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    # Check for invite a team member button
    invite_team_member_button = page.get_by_role("button", name="Invite a team member")
    expect(invite_team_member_button).to_be_visible()
    invite_team_member_button.click()

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    # Fill and check email address value.
    email_address_input = page.get_by_label("Email address")
    email_address_input.fill("e2esupertestuser@gsa.gov")
    expect(email_address_input).to_have_value("e2esupertestuser@gsa.gov")

    permissions = [
        "See dashboard",
        "Send messages",
        "Add and edit templates",
        "Manage settings, team and usage",
        "Manage API integration",
    ]

    # Check permission labels are on page
    for permission in permissions:
        expect(page.get_by_label(permission)).to_be_visible

    # There is an issue with checking the send messages box due to possible duplicate
    # "Send messages" appearing on the page.
    # Put checkboxes into checked state.
    checkbox_list = [
        "See dashboard",
        "Add and edit templates",
        "Manage settings, team and usage",
        "Manage API integration",
    ]

    for checkbox in checkbox_list:
        page.check(f"text={checkbox}", force=True)

        permission_box_activity = page.get_by_role("checkbox", name=checkbox)
        expect(permission_box_activity).to_be_checked()

    # Check for send invitation email button
    send_invite_email_button = page.get_by_role(
        "button", name=re.compile("Send invitation email")
    )
    expect(send_invite_email_button).to_be_visible()
    # send_invite_email_button.click()
    # Check to make sure that we've arrived at the next page.
    # page.wait_for_load_state("domcontentloaded")
    # Check invite sent text appears on page.
    # assert "Invite sent to e2esupertestuser@gsa.gov" in page.content()

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
