import pytest
from freezegun import freeze_time

from app.main.forms import ChooseTimeForm


@freeze_time("2016-01-01 16:09:00.061258")
def test_form_contains_next_24h(notify_admin):

    choices = ChooseTimeForm().scheduled_for.choices

    # Friday
    assert choices[0] == ('', 'Now')
    assert choices[1] == ('2016-01-01T17:00:00', 'Today at noon ET')
    assert choices[13] == ('2016-01-02T05:00:00', 'Today at midnight ET')

    # Saturday
    assert choices[14] == ('2016-01-02T06:00:00', 'Tomorrow at 1am ET')
    assert choices[37] == ('2016-01-03T05:00:00', 'Tomorrow at midnight ET')

    # Sunday
    assert choices[38] == ('2016-01-03T06:00:00', 'Sunday at 1am ET')

    # Monday
    assert choices[62] == ('2016-01-04T06:00:00', 'Monday at 1am ET')
    assert choices[80] == ('2016-01-05T00:00:00', 'Monday at 7pm ET')
    assert choices[84] == ('2016-01-05T04:00:00', 'Monday at 11pm ET')
    assert choices[85] == ('2016-01-05T05:00:00', 'Monday at midnight ET')

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
