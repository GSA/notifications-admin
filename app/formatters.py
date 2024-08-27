import os
import re
import unicodedata
import urllib
from datetime import datetime, timedelta, timezone
from functools import partial
from math import floor, log10
from numbers import Number

import ago
import dateutil
import humanize
import markdown
import pytz
from bs4 import BeautifulSoup
from flask import render_template_string, url_for
from flask.helpers import get_root_path
from markupsafe import Markup

from app.utils.csv import get_user_preferred_timezone
from app.utils.time import parse_naive_dt
from notifications_utils.field import Field
from notifications_utils.formatters import make_quotes_smart
from notifications_utils.formatters import nl2br as utils_nl2br
from notifications_utils.recipients import InvalidPhoneError, validate_phone_number
from notifications_utils.take import Take


def apply_html_class(tags, html_file):
    new_html = html_file

    for tag in tags:
        element = tag[0]
        class_name = tag[1]

        soup = BeautifulSoup(new_html, "html.parser")

        for xtag in soup.find_all(element):
            xtag["class"] = class_name

        new_html = str(soup)

    return new_html


def convert_markdown_template(mdf, test=False):
    content_text = ""

    if not test:
        APP_ROOT = get_root_path("notifications-admin")
        file = "app/content/" + mdf + ".md"
        md_file = os.path.join(APP_ROOT, file)
        with open(md_file) as f:
            content_text = f.read()
    else:
        content_text = mdf

    jn_render = render_template_string(content_text)
    md_render = markdown.markdown(jn_render)

    return md_render


def convert_to_boolean(value):
    if isinstance(value, str):
        if value.lower() in ["t", "true", "on", "yes", "1"]:
            return True
        elif value.lower() in ["f", "false", "off", "no", "0"]:
            return False

    return value


def format_datetime(date):
    return "{} at {} {}".format(
        format_date(date), format_time_24h(date), get_user_preferred_timezone()
    )


def format_datetime_24h(date):
    return "{} at {} {}".format(
        format_date(date), format_time_24h(date), get_user_preferred_timezone()
    )


def format_time(date):
    return format_datetime_24h(date)


def format_datetime_normal(date):
    # example: February 20, 2024 at 07:00 PM US/Eastern, used for datetimes that's not within tables
    return "{} at {} {}".format(
        format_date_normal(date), format_time_12h(date), get_user_preferred_timezone()
    )


def format_datetime_scheduled_notification(date):
    # e.g. April 09, 2024 at 04:00 PM US/Eastern.
    # Everything except scheduled notifications, the time is always "now".
    # Scheduled notifications are the exception to the rule.
    # Here we are formating and displaying the datetime without converting datetime to a different timezone.

    datetime_obj = parse_naive_dt(date)

    format_time_without_tz = datetime_obj.replace(tzinfo=timezone.utc).strftime(
        "%I:%M %p"
    )
    return "{} at {} {}".format(
        format_date_normal(date), format_time_without_tz, get_user_preferred_timezone()
    )


def format_datetime_table(date):
    # example:  03-18-2024 at 04:53 PM, intended for datetimes in tables
    return "{} at {}".format(format_date_numeric(date), format_time_12h(date))


def format_time_12h(date):
    date = parse_naive_dt(date)

    preferred_tz = pytz.timezone(get_user_preferred_timezone())
    return (
        date.replace(tzinfo=timezone.utc).astimezone(preferred_tz).strftime("%I:%M %p")
    )


def format_datetime_relative(date):
    return "{} at {} {}".format(
        get_human_day(date), format_time_24h(date), get_user_preferred_timezone()
    )


def format_datetime_numeric(date):
    return "{} {} {}".format(
        format_date_numeric(date), format_time_24h(date), get_user_preferred_timezone()
    )


def format_date_numeric(date):
    date = parse_naive_dt(date)

    preferred_tz = pytz.timezone(get_user_preferred_timezone())
    return (
        date.replace(tzinfo=timezone.utc).astimezone(preferred_tz).strftime("%m-%d-%Y")
    )


def format_time_24h(date):
    date = parse_naive_dt(date)

    preferred_tz = pytz.timezone(get_user_preferred_timezone())
    return date.replace(tzinfo=timezone.utc).astimezone(preferred_tz).strftime("%H:%M")


def get_human_day(time, date_prefix=""):
    #  Add 1 minute to transform 00:00 into ‘midnight today’ instead of ‘midnight tomorrow’
    time = parse_naive_dt(time)
    preferred_tz = pytz.timezone(get_user_preferred_timezone())
    time = time.replace(tzinfo=timezone.utc).astimezone(preferred_tz)
    date = (time - timedelta(minutes=1)).date()
    now = datetime.now(preferred_tz)

    if date == (now + timedelta(days=1)).date():
        return "tomorrow"
    if date == now.date():
        return "today"
    if date == (now - timedelta(days=1)).date():
        return "yesterday"
    if date.strftime("%Y") != now.strftime("%Y"):
        return "{} {} {}".format(
            date_prefix,
            _format_datetime_short(date),
            date.strftime("%Y"),
        ).strip()
    return "{} {}".format(
        date_prefix,
        _format_datetime_short(date),
    ).strip()


def format_date(date):
    date = parse_naive_dt(date)
    preferred_tz = pytz.timezone(get_user_preferred_timezone())
    return (
        date.replace(tzinfo=timezone.utc)
        .astimezone(preferred_tz)
        .strftime("%A %d %B %Y")
    )


def format_date_normal(date):
    date = parse_naive_dt(date)
    return date.strftime("%B %d, %Y").lstrip("0")


def format_date_short(date):
    date = parse_naive_dt(date)
    preferred_tz = pytz.timezone(get_user_preferred_timezone())
    return _format_datetime_short(
        date.replace(tzinfo=timezone.utc).astimezone(preferred_tz)
    )


def format_date_human(date):
    return get_human_day(date)


def format_datetime_human(date, date_prefix=""):
    return "{} at {} {}".format(
        get_human_day(date, date_prefix="on"),
        format_time_24h(date),
        get_user_preferred_timezone(),
    )


def format_day_of_week(date):
    date = parse_naive_dt(date)
    preferred_tz = pytz.timezone(get_user_preferred_timezone())
    return date.replace(tzinfo=timezone.utc).astimezone(preferred_tz).strftime("%A")


def _format_datetime_short(datetime):
    return datetime.strftime("%d %B").lstrip("0")


def naturaltime_without_indefinite_article(date):
    return re.sub(
        "an? (.*) ago",
        lambda match: "1 {} ago".format(match.group(1)),
        humanize.naturaltime(date),
    )


def convert_time_unixtimestamp(date_string):
    dt = datetime.fromisoformat(date_string)
    return int(dt.timestamp())


def format_delta(date):
    # This method assumes that date is in UTC
    date = parse_naive_dt(date)
    delta = (datetime.utcnow()) - (date)
    if delta < timedelta(seconds=30):
        return "just now"
    if delta < timedelta(seconds=60):
        return "in the last minute"
    return naturaltime_without_indefinite_article(delta)


def format_delta_days(date):
    # This method assumes that date is in UTC
    date = parse_naive_dt(date)
    now = datetime.utcnow()
    if date.strftime("%Y-%m-%d") == now.strftime("%Y-%m-%d"):
        return "today"
    if date.strftime("%Y-%m-%d") == (now - timedelta(days=1)).strftime("%Y-%m-%d"):
        return "yesterday"
    return naturaltime_without_indefinite_article(now - date)


def valid_phone_number(phone_number):
    try:
        validate_phone_number(phone_number)
        return True
    except InvalidPhoneError:
        return False


def format_notification_type(notification_type):
    return {
        "email": "Email",
        "sms": "Text message",
    }[notification_type]


def format_notification_status(status, template_type):
    return {
        "email": {
            "failed": "Failed",
            "technical-failure": "Technical failure",
            "temporary-failure": "Inbox not accepting messages right now",
            "permanent-failure": "Email address does not exist",
            "delivered": "Delivered",
            "sending": "Sending",
            "created": "Sending",
            "sent": "Delivered",
        },
        "sms": {
            "failed": "Failed",
            "technical-failure": "Technical failure",
            "temporary-failure": "Phone not accepting messages right now",
            "permanent-failure": "Not delivered",
            "delivered": "Delivered",
            "sending": "Sending",
            "created": "Sending",
            "pending": "Sending",
            "sent": "Sent",
        },
    }[template_type].get(status, status)


def format_notification_status_as_time(status, created, updated):
    return dict.fromkeys(
        {"created", "pending", "sending"}, " since {}".format(created)
    ).get(status, updated)


def format_notification_status_as_field_status(status, notification_type):
    return {
        "failed": "error",
        "technical-failure": "error",
        "temporary-failure": "error",
        "permanent-failure": "error",
        "delivered": None,
        "sent": "sent-international" if notification_type == "sms" else None,
        "sending": "default",
        "created": "default",
        "pending": "default",
    }.get(status, "error")


def format_notification_status_as_url(status, notification_type):
    url = partial(url_for, "main.message_status")

    if status not in {
        "technical-failure",
        "temporary-failure",
        "permanent-failure",
    }:
        return None

    return {
        "email": url(_anchor="email-statuses"),
        "sms": url(_anchor="text-message-statuses"),
    }.get(notification_type)


def nl2br(value):
    if value:
        return Markup(
            Take(
                Field(
                    value,
                    html="escape",
                )
            ).then(utils_nl2br)
        )
    return ""


# this formatter appears to only be used in the letter module
# TODO: use more widely, or delete? currency symbol could be set in config
def format_number_in_pounds_as_currency(number):
    if number >= 1:
        return f"£{number:,.2f}"

    return f"{number * 100:.0f}p"


def format_list_items(items, format_string, *args, **kwargs):
    """
    Apply formatting to each item in an iterable. Returns a list.
    Each item is made available in the format_string as the 'item' keyword argument.
    example usage: ['png','svg','pdf']|format_list_items('{0}. {item}', [1,2,3]) -> ['1. png', '2. svg', '3. pdf']
    """
    return [format_string.format(*args, item=item, **kwargs) for item in items]


def linkable_name(value):
    return urllib.parse.quote_plus(value)


def format_thousands(value):
    if isinstance(value, Number):
        return "{:,.0f}".format(value)
    if value is None:
        return ""
    return value


def email_safe(string, whitespace="."):
    # strips accents, diacritics etc
    string = "".join(
        c
        for c in unicodedata.normalize("NFD", string)
        if unicodedata.category(c) != "Mn"
    )
    string = "".join(
        word.lower() if word.isalnum() or word == whitespace else ""
        for word in re.sub(r"\s+", whitespace, string.strip())
    )
    string = re.sub(r"\.{2,}", ".", string)
    return string.strip(".")


def id_safe(string):
    return email_safe(string, whitespace="-")


def round_to_significant_figures(value, number_of_significant_figures):
    if value == 0:
        return value
    return int(
        round(value, number_of_significant_figures - int(floor(log10(abs(value)))) - 1)
    )


def redact_mobile_number(mobile_number, spacing=""):
    indices = [-4, -5, -6, -7]
    redact_character = spacing + "•" + spacing
    mobile_number_list = list(mobile_number.replace(" ", ""))
    for i in indices:
        mobile_number_list[i] = redact_character
    return "".join(mobile_number_list)


def get_time_left(created_at, service_data_retention_days=7):
    return ago.human(
        (datetime.now(timezone.utc))
        - (
            dateutil.parser.parse(created_at).replace(hour=0, minute=0, second=0)
            + timedelta(days=service_data_retention_days + 1)
        ),
        future_tense="Data available for {}",
        past_tense="Data no longer available",  # No-one should ever see this
        precision=1,
    )


def starts_with_initial(name):
    return bool(re.match(r"^.\.", name))


def remove_middle_initial(name):
    return re.sub(r"\s+.\s+", " ", name)


def remove_digits(name):
    return "".join(c for c in name if not c.isdigit())


def normalize_spaces(name):
    return " ".join(name.split())


def guess_name_from_email_address(email_address):
    possible_name = re.split(r"[\@\+]", email_address)[0]

    if "." not in possible_name or starts_with_initial(possible_name):
        return ""

    return (
        Take(possible_name)
        .then(str.replace, ".", " ")
        .then(remove_digits)
        .then(remove_middle_initial)
        .then(str.title)
        .then(make_quotes_smart)
        .then(normalize_spaces)
    )


def message_count_label(count, template_type, suffix="sent"):
    if suffix:
        return f"{message_count_noun(count, template_type)} {suffix}"
    return message_count_noun(count, template_type)


def message_count_noun(count, template_type):
    if template_type is None:
        if count == 1:
            return "message"
        else:
            return "messages"

    if template_type == "sms":
        if count == 1:
            return "text message"
        else:
            return "text messages"

    if template_type == "parts":
        if count == 1:
            return "text message part"
        else:
            return "text message parts"

    elif template_type == "email":
        if count == 1:
            return "email"
        else:
            return "emails"


def message_count(count, template_type):
    return f"{format_thousands(count)} " f"{message_count_noun(count, template_type)}"


def recipient_count_label(count, template_type):
    if template_type is None:
        if count == 1:
            return "recipient"
        else:
            return "recipients"

    if template_type == "sms":
        if count == 1:
            return "phone number"
        else:
            return "phone numbers"

    elif template_type == "email":
        if count == 1:
            return "email address"
        else:
            return "email addresses"


def recipient_count(count, template_type):
    return (
        f"{format_thousands(count)} " f"{recipient_count_label(count, template_type)}"
    )


def iteration_count(count):
    if count == 1:
        return "once"
    elif count == 2:
        return "twice"
    else:
        return f"{count} times"


def character_count(count):
    if count == 1:
        return "1 character"
    return f"{format_thousands(count)} characters"


def format_mobile_network(network):
    if network in ("three", "vodafone", "o2"):
        return network.capitalize()
    return "EE"


def format_billions(count):
    return humanize.intword(count)


def format_yes_no(value, yes="Yes", no="No", none="No"):
    if value is None:
        return none
    return yes if value else no


def square_metres_to_square_miles(area):
    return area * 3.86e-7


def format_auth_type(auth_type, with_indefinite_article=False):
    indefinite_article, auth_type = {
        "email_auth": ("an", "Email link"),
        "sms_auth": ("a", "Text message code"),
    }[auth_type]

    if with_indefinite_article:
        return f"{indefinite_article} {auth_type.lower()}"

    return auth_type
