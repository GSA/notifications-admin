import os

from axe_core_python.sync_playwright import Axe

E2E_TEST_URI = os.getenv("NOTIFY_E2E_TEST_URI")


def test_a11y(authenticated_page, end_to_end_context):
    page = authenticated_page

    # Prepare for adding a new service later in the test.
    # current_date_time = datetime.datetime.now()
    # new_service_name = "E2E Federal Test Service {now} - {browser_type}".format(
    #    now=current_date_time.strftime("%m/%d/%Y %H:%M:%S"),
    #    browser_type=end_to_end_context.browser.browser_type.name,
    # )

    page.goto(f"{E2E_TEST_URI}/accounts")

    # Check to make sure that we've arrived at the next page.
    page.wait_for_load_state("domcontentloaded")

    axe = Axe()

    results = axe.run(page)

    assert (
        len(results["violations"]) == 0
    ), f"Accessibility violations: {results['violations']}"
