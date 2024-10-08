import pytest
from freezegun import freeze_time

from app.utils.time import get_current_financial_year, is_less_than_days_ago


@pytest.mark.parametrize(
    ("date_from_db", "expected_result"),
    [
        ("2019-11-17T11:35:21.726132Z", True),
        ("2019-11-16T11:35:21.726132Z", False),
        ("2019-11-16T11:35:21+0000", False),
    ],
)
@freeze_time("2020-02-14T12:00:00")
def test_is_less_than_days_ago(date_from_db, expected_result):
    assert is_less_than_days_ago(date_from_db, 90) == expected_result
