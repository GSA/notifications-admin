import pytest
from freezegun import freeze_time

from app.main.forms import ChooseTimeForm


@freeze_time("2016-01-01 11:09:00.061258")
def test_form_contains_next_24h(notify_admin):
    choices = ChooseTimeForm().scheduled_for.choices

    # Friday
    assert choices[0] == ("", "Now")
    assert choices[1] == ("2016-01-01T07:00:00-05:00", "Today at 7am US/Eastern")
    assert choices[13] == ("2016-01-01T19:00:00-05:00", "Today at 7pm US/Eastern")

    # Saturday
    assert choices[14] == ("2016-01-01T20:00:00-05:00", "Today at 8pm US/Eastern")
    assert choices[37] == ("2016-01-02T19:00:00-05:00", "Tomorrow at 7pm US/Eastern")

    # Sunday
    assert choices[38] == ("2016-01-02T20:00:00-05:00", "Tomorrow at 8pm US/Eastern")

    # Monday
    assert choices[62] == ("2016-01-03T20:00:00-05:00", "Sunday at 8pm US/Eastern")
    assert choices[80] == ("2016-01-04T14:00:00-05:00", "Monday at 2pm US/Eastern")
    assert choices[84] == ("2016-01-04T18:00:00-05:00", "Monday at 6pm US/Eastern")
    assert choices[85] == ("2016-01-04T19:00:00-05:00", "Monday at 7pm US/Eastern")

    with pytest.raises(IndexError):
        assert choices[
            17 + (3 * 24) + 2  # hours left in the day  # 3 days  # magic number
        ]


@freeze_time("2016-01-01 11:09:00.061258")
def test_form_defaults_to_now(notify_admin):
    assert ChooseTimeForm().scheduled_for.data == ""


@freeze_time("2016-01-01 11:09:00.061258")
def test_form_contains_next_three_days(notify_admin):
    assert ChooseTimeForm().scheduled_for.categories == [
        "Later today",
        "Tomorrow",
        "Sunday",
        "Monday",
    ]
