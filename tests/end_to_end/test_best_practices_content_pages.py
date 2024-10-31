import os
import re

from playwright.sync_api import expect

from tests.end_to_end.conftest import check_axe_report

E2E_TEST_URI = os.getenv("NOTIFY_E2E_TEST_URI")


def test_best_practices_side_menu(authenticated_page):
    page = authenticated_page

    page.goto(f"{E2E_TEST_URI}/best-practices")

    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    page.get_by_role("link", name="Best Practices").click()
    expect(page).to_have_title(re.compile("Best Practice"))

    page.get_by_role("link", name="Clear goals", exact=True).click()
    expect(page).to_have_title(re.compile("Establish clear goals"))

    page.get_by_role("link", name="Rules and regulations").click()
    expect(page).to_have_title(re.compile("Rules and regulations"))

    page.get_by_role("link", name="Establish trust").click()
    expect(page).to_have_title(re.compile("Establish trust"))

    page.get_by_role("link", name="Write for action").click()
    expect(page).to_have_title(re.compile("Write texts that provoke"))

    page.get_by_role("link", name="Multiple languages").click()
    expect(page).to_have_title(re.compile("Text in multiple languages"))

    page.get_by_role("link", name="Benchmark performance").click()
    expect(page).to_have_title(re.compile("Measuring performance with"))

    parent_link = page.get_by_role("link", name="Establish trust")
    parent_link.hover()

    submenu_item = page.get_by_role("link", name=re.compile("Get the word out"))
    submenu_item.click()

    expect(page).to_have_url(re.compile(r"#get-the-word-out"))

    anchor_target = page.locator("#get-the-word-out")
    expect(anchor_target).to_be_visible()
    anchor_target.click()


def test_breadcrumbs_best_practices(authenticated_page):
    page = authenticated_page

    page.goto(f"{E2E_TEST_URI}/best-practices")

    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)

    page.get_by_role("link", name="Clear goals", exact=True).click()
    page.locator("ol").get_by_role("link", name="Best Practices").click()
