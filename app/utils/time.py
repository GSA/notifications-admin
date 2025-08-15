from datetime import datetime
from zoneinfo import ZoneInfo

from dateutil import parser

from app.utils.csv import get_user_preferred_timezone_obj


def get_current_financial_year():
    preferred_tz = get_user_preferred_timezone_obj()
    now = datetime.now(preferred_tz)
    current_year = int(now.strftime("%Y"))
    return current_year


def is_less_than_days_ago(date_from_db, number_of_days):
    return (
        datetime.now(ZoneInfo("UTC")) - parser.parse(date_from_db)
    ).days < number_of_days


def parse_naive_dt(dt):
    return parser.parse(dt, ignoretz=True)
