import datetime
import os

import pytest
from axe_core_python.sync_playwright import Axe
from playwright.sync_api import Page

E2E_TEST_URI = os.getenv("NOTIFY_E2E_TEST_URI")


@pytest.fixture
def end_to_end_context(browser):
    context = browser.new_context()
    return context


@pytest.fixture
def authenticated_page(end_to_end_context):
    page = end_to_end_context.new_page()
    page.goto(f"{E2E_TEST_URI}/sign-in")
    page.wait_for_load_state("domcontentloaded")
    return page


def check_axe_report(page):
    axe = Axe()
    results = axe.run(page)

    filtered_violations = []
    for violation in results["violations"]:
        keep = True
        for node in violation["nodes"]:
            for target in node.get("target", []):
                # Skip known Flask debug elements like werkzeug or debugger footer
                if (
                    "werkzeug" in target
                    or ".debugger" in target
                    or ".footer" in target
                    or "DON'T PANIC" in node.get("html", "")
                ):
                    keep = False
        if keep:
            filtered_violations.append(violation)

    for violation in filtered_violations:
        assert violation["impact"] in [
            "minor",
            "moderate",
        ], f"Accessibility violation: {violation}"


@pytest.fixture(autouse=True)
def _mock_common_api_calls(mocker):
    # Patch the health check so it doesn't hit external endpoints
    mocker.patch("app.utils.api_health.is_api_down", return_value=False)

    # Add more global mocks as needed, like:
    mocker.patch(
        "app.service_api_client.get_service",
        return_value={"id": "1234", "name": "Test Service"},
    )

    # Optional: silence New Relic or other external integrations
    mocker.patch("newrelic.agent.initialize", return_value=None)


@pytest.fixture
def e2e_test_service(authenticated_page: Page, end_to_end_context):
    """
    Creates a test service for E2E tests with guaranteed cleanup.

    This fixture ensures services are deleted even if tests fail, preventing
    database pollution from abandoned E2E test services.
    """
    page = authenticated_page
    current_date_time = datetime.datetime.now()
    service_name = "E2E Federal Test Service {now} - {browser_type}".format(
        now=current_date_time.strftime("%m/%d/%Y %H:%M:%S"),
        browser_type=end_to_end_context.browser.browser_type.name,
    )

    service_info = {
        "name": service_name,
        "page": page,
    }

    yield service_info

    # runs even if test fails
    try:
        _cleanup_test_service(page, service_name)
    except Exception as e:
        print(f"Warning: Failed to cleanup service '{service_name}': {e}")  # noqa: T201


@pytest.fixture
def e2e_created_service(e2e_test_service):  # noqa: PT022
    """
    Creates a test service AND completes the service creation workflow.

    This fixture not only generates a unique service name but also creates
    the service through the UI, providing a ready-to-use service for tests.
    """
    service_info = e2e_test_service
    page = service_info["page"]
    service_name = service_info["name"]

    page.goto(f"{E2E_TEST_URI}/accounts")
    page.wait_for_load_state("domcontentloaded")

    add_service_button = page.get_by_role("button", name="Add a new service")
    add_service_button.click()
    page.wait_for_load_state("domcontentloaded")

    service_name_input = page.locator('xpath=//input[@name="name"]')
    service_name_input.fill(service_name)

    add_button = page.get_by_role("button", name="Add service")
    add_button.click()
    page.wait_for_load_state("domcontentloaded")

    service_info["url"] = page.url

    yield service_info


def _cleanup_test_service(page: Page, service_name: str):
    """
    Delete a test service by navigating to its settings and clicking delete.

    Args:
        page: Playwright page object
        service_name: Name of the service to delete
    """
    try:
        page.goto(f"{E2E_TEST_URI}/accounts")
        page.wait_for_load_state("domcontentloaded")

        service_link = page.get_by_role("link", name=service_name)

        if service_link.count() > 0:
            service_link.click()
            page.wait_for_load_state("domcontentloaded")

            page.click("text='Settings'")
            page.wait_for_load_state("domcontentloaded")

            page.click("text='Delete this service'")
            page.wait_for_load_state("domcontentloaded")

            page.click("text='Yes, delete'")
            page.wait_for_load_state("domcontentloaded")

            print(f"Successfully cleaned up test service: {service_name}")  # noqa: T201
        else:
            print(  # noqa: T201
                f"Service '{service_name}' not found, may have been deleted already"
            )

    except Exception as e:
        raise Exception(f"Failed to cleanup service '{service_name}': {str(e)}")
