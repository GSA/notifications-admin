import pytest
from freezegun import freeze_time

from app.main.forms import ChooseTimeForm


@freeze_time("2016-01-01 16:09:00.061258")
def test_form_contains_next_24h(notify_admin):

    choices = ChooseTimeForm().scheduled_for.choices

    # Friday
    assert choices[0] == ('', 'Now')
    assert choices[1] == ('2016-01-01T12:00:00', 'Today at noon UTC')
    assert choices[13] == ('2016-01-02T00:00:00', 'Today at midnight UTC')

    # Saturday
    assert choices[14] == ('2016-01-02T06:00:00', 'Tomorrow at 6am UTC')
    assert choices[37] == ('2016-01-03T00:00:00', 'Tomorrow at midnight UTC')

    # Sunday
    assert choices[38] == ('2016-01-03T06:00:00', 'Sunday at 6am UTC')

    # Monday
    assert choices[62] == ('2016-01-04T00:00:00', 'Today at midnight UTC')
    assert choices[80] == ('2016-01-05T12:00:00', 'Monday at noon UTC')
    assert choices[84] == ('2016-01-05T19:00:00', 'Monday at 7pm UTC')
    assert choices[85] == ('2016-01-05T00:00:00', 'Monday at midnight UTC')

    with pytest.raises(IndexError):
        assert choices[
            12 +        # hours left in the day
            (3 * 24) +  # 3 days
            2           # magic number
        ]


@freeze_time("2016-01-01 11:09:00.061258")
def test_form_defaults_to_now(notify_admin):
    assert ChooseTimeForm().scheduled_for.data == ''


@freeze_time("2016-01-01 11:09:00.061258")
def test_form_contains_next_three_days(notify_admin):
    assert ChooseTimeForm().scheduled_for.categories == [
        'Later today', 'Tomorrow', 'Sunday', 'Monday'
    ]
