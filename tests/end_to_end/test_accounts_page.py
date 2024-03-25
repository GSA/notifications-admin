import datetime
import os
import re

from playwright.sync_api import expect

E2E_TEST_URI = os.getenv("NOTIFY_E2E_TEST_URI")


def test_add_new_service_workflow(authenticated_page, end_to_end_context):
    pass
