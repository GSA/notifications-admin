import os
import re
from playwright.sync_api import expect
from tests.end_to_end.conftest import check_axe_report

E2E_TEST_URI = os.getenv("NOTIFY_E2E_TEST_URI")


def test_sign_in_redirects_when_authenticated(authenticated_page):
    page = authenticated_page
    page.goto(f"{E2E_TEST_URI}/accounts")
    page.wait_for_load_state("domcontentloaded")
    check_axe_report(page)
    expect(page).to_have_url(re.compile("/accounts"))
    expect(page).to_have_title(re.compile("Choose service"))
