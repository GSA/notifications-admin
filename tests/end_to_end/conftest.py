import os

import pytest
from axe_core_python.sync_playwright import Axe

E2E_TEST_URI = os.getenv("NOTIFY_E2E_TEST_URI")


@pytest.fixture
def end_to_end_context(browser):
    context = browser.new_context()
    return context


@pytest.fixture
def authenticated_page(end_to_end_context):
    # Open a new page and go to the site.
    page = end_to_end_context.new_page()
    page.goto(f"{E2E_TEST_URI}/sign-in")

    # Wait for the next page to fully load.
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
    mocker.patch("app.utils.api_health.check_api_is_running", return_value=True)

    # If ping_json_endpoint is used directly instead
    mocker.patch(
        "app.utils.api_health.ping_json_endpoint", return_value={"status": "ok"}
    )

    # Add more global mocks as needed, like:
    mocker.patch(
        "app.service_api_client.get_service",
        return_value={"id": "1234", "name": "Test Service"},
    )

    # Optional: silence New Relic or other external integrations
    mocker.patch("newrelic.agent.initialize", return_value=None)
