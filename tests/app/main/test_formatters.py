from datetime import datetime
from functools import partial

import pytest
from flask import Flask, url_for
from freezegun import freeze_time

from app.formatters import (
    apply_html_class,
    convert_markdown_template,
    email_safe,
    format_datetime_relative,
    format_delta,
    format_notification_status_as_url,
    format_number_in_pounds_as_currency,
    round_to_significant_figures,
)


@pytest.mark.parametrize(
    ("status", "notification_type", "expected"),
    [
        # Successful statuses aren’t linked
        ("created", "email", lambda: None),
        ("sending", "email", lambda: None),
        ("delivered", "email", lambda: None),
        # Failures are linked to the channel-specific page
        (
            "temporary-failure",
            "email",
            partial(url_for, "main.message_status", _anchor="email-statuses"),
        ),
        (
            "permanent-failure",
            "email",
            partial(url_for, "main.message_status", _anchor="email-statuses"),
        ),
        (
            "technical-failure",
            "email",
            partial(url_for, "main.message_status", _anchor="email-statuses"),
        ),
        (
            "temporary-failure",
            "sms",
            partial(url_for, "main.message_status", _anchor="text-message-statuses"),
        ),
        (
            "permanent-failure",
            "sms",
            partial(url_for, "main.message_status", _anchor="text-message-statuses"),
        ),
        (
            "technical-failure",
            "sms",
            partial(url_for, "main.message_status", _anchor="text-message-statuses"),
        ),
    ],
)
def test_format_notification_status_as_url(
    client_request,
    status,
    notification_type,
    expected,
):
    assert format_notification_status_as_url(status, notification_type) == expected()


@pytest.mark.parametrize(
    ("input_number", "formatted_number"),
    [
        (0, "0p"),
        (0.01, "1p"),
        (0.5, "50p"),
        (1, "£1.00"),
        (1.01, "£1.01"),
        (1.006, "£1.01"),
        (5.25, "£5.25"),
        (5.7, "£5.70"),
        (381, "£381.00"),
        (144820, "£144,820.00"),
    ],
)
def test_format_number_in_pounds_as_currency(input_number, formatted_number):
    assert format_number_in_pounds_as_currency(input_number) == formatted_number


@pytest.mark.parametrize(
    ("time", "human_readable_datetime"),
    [
        # incoming in UTC, outgoing in "human formatted" UTC
        ("2018-03-14 09:00", "14 March at 05:00 US/Eastern"),
        ("2018-03-14 19:00", "14 March at 15:00 US/Eastern"),
        ("2018-03-15 09:00", "15 March at 05:00 US/Eastern"),
        ("2018-03-15 19:00", "15 March at 15:00 US/Eastern"),
        ("2018-03-19 09:00", "19 March at 05:00 US/Eastern"),
        ("2018-03-19 19:00", "19 March at 15:00 US/Eastern"),
        ("2018-03-19 23:59", "19 March at 19:59 US/Eastern"),
        (
            "2018-03-20 04:00",
            "19 March at 00:00 US/Eastern",
        ),  # we specifically refer to 00:00 as belonging to the day before.
        ("2018-03-20 04:01", "yesterday at 00:01 US/Eastern"),
        ("2018-03-20 09:00", "yesterday at 05:00 US/Eastern"),
        ("2018-03-20 19:00", "yesterday at 15:00 US/Eastern"),
        ("2018-03-20 23:59", "yesterday at 19:59 US/Eastern"),
        (
            "2018-03-21 04:00",
            "yesterday at 00:00 US/Eastern",
        ),  # we specifically refer to 00:00 as belonging to the day before.
        ("2018-03-21 04:01", "today at 00:01 US/Eastern"),
        ("2018-03-21 09:00", "today at 05:00 US/Eastern"),
        ("2018-03-21 12:00", "today at 08:00 US/Eastern"),
        ("2018-03-21 19:00", "today at 15:00 US/Eastern"),
        ("2018-03-21 23:59", "today at 19:59 US/Eastern"),
        ("2018-03-22 00:00", "today at 20:00 US/Eastern"),
        ("2018-03-22 04:01", "tomorrow at 00:01 US/Eastern"),
        ("2018-03-22 09:00", "tomorrow at 05:00 US/Eastern"),
        ("2018-03-22 19:00", "tomorrow at 15:00 US/Eastern"),
        ("2018-03-22 23:59", "tomorrow at 19:59 US/Eastern"),
        ("2018-03-23 04:01", "23 March at 00:01 US/Eastern"),
        ("2018-03-23 09:00", "23 March at 05:00 US/Eastern"),
        ("2018-03-23 19:00", "23 March at 15:00 US/Eastern"),
    ],
)
def test_format_datetime_relative(time, human_readable_datetime):
    with freeze_time("2018-03-21 12:00"):
        assert format_datetime_relative(time) == human_readable_datetime


@pytest.mark.parametrize(
    ("value", "significant_figures", "expected_result"),
    [
        (0, 1, 0),
        (0, 2, 0),
        (12_345, 1, 10_000),
        (12_345, 2, 12_000),
        (12_345, 3, 12_300),
        (12_345, 9, 12_345),
        (12_345.6789, 1, 10_000),
        (12_345.6789, 9, 12_345),
        (-12_345, 1, -10_000),
    ],
)
def test_round_to_significant_figures(value, significant_figures, expected_result):
    assert round_to_significant_figures(value, significant_figures) == expected_result


@pytest.mark.parametrize(
    ("service_name", "safe_email"),
    [
        ("name with spaces", "name.with.spaces"),
        ("singleword", "singleword"),
        ("UPPER CASE", "upper.case"),
        ("Service - with dash", "service.with.dash"),
        ("lots      of spaces", "lots.of.spaces"),
        ("name.with.dots", "name.with.dots"),
        ("name-with-other-delimiters", "namewithotherdelimiters"),
        (".leading", "leading"),
        ("trailing.", "trailing"),
        ("üńïçödë wördś", "unicode.words"),
    ],
)
def test_email_safe_return_dot_separated_email_domain(service_name, safe_email):
    assert email_safe(service_name) == safe_email


def test_format_delta():
    naive_now_utc = datetime.utcnow().isoformat()
    assert format_delta(naive_now_utc) == "just now"


@pytest.mark.usefixtures("fake_jinja_template")
def test_jinja_format(fake_jinja_template):
    app = Flask("app")
    with app.app_context():
        assert (
            convert_markdown_template(fake_jinja_template, test=True) == "<p>True</p>"
        )


@pytest.mark.usefixtures("fake_markdown_file")
def test_markdown_format(fake_markdown_file):
    app = Flask("app")
    with app.app_context():
        assert (
            convert_markdown_template(fake_markdown_file, test=True) == "<h1>Test</h1>"
        )


@pytest.mark.usefixtures("fake_soup_template")
def test_soup_format(fake_soup_template):
    assert (
        apply_html_class([["h1", "testClass"]], fake_soup_template)
        == '<h1 class="testClass">Test</h1>'
    )
