import os
import re

from playwright.sync_api import expect

from tests.end_to_end.conftest import check_axe_report

E2E_TEST_URI = os.getenv("NOTIFY_E2E_TEST_URI")


def test_best_practices_side_menu(authenticated_page):
    page = authenticated_page

    page.goto(f"{E2E_TEST_URI}/guides/best-practices")
    page.wait_for_load_state("networkidle")
    check_axe_report(page)

    # Test navigation for "Best Practices" and its sub-links
    expect(page.get_by_role("link", name="Best Practices")).to_be_visible(timeout=10000)

    # Test the individual sublinks under Best Practices
    page.get_by_role("link", name="Clear goals", exact=True).click()
    expect(page).to_have_title(re.compile("Clear goals"))

    page.get_by_role("link", name="Rules and regulations").click()
    expect(page).to_have_title(re.compile("Rules and regulations"))

    page.get_by_role("link", name="Establish trust").click()
    expect(page).to_have_title(re.compile("Establish trust"))

    page.get_by_role("link", name="Write for action").click()
    expect(page).to_have_title(re.compile("Write for action"))

    page.get_by_role("link", name="Multiple languages").click()
    expect(page).to_have_title(re.compile("Multiple languages"))

    page.get_by_role("link", name="Benchmark performance").click()
    expect(page).to_have_title(re.compile("Benchmark performance"))


def test_breadcrumbs_best_practices(authenticated_page):
    page = authenticated_page

    page.goto(f"{E2E_TEST_URI}/guides/best-practices")
    page.wait_for_load_state("networkidle")
    check_axe_report(page)

    # Test breadcrumb navigation from a subpage
    page.get_by_role("link", name="Clear goals", exact=True).click()
    breadcrumb_link = page.locator("ol").get_by_role("link", name="Best Practices")
    expect(breadcrumb_link).to_be_visible(timeout=10000)
    breadcrumb_link.click()
    expect(page).to_have_title(re.compile("Best Practices"))
