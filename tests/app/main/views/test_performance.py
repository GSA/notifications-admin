import random
import uuid
from datetime import date

from freezegun import freeze_time

from tests.conftest import normalize_spaces


def _get_example_performance_data():
    return {
      "total_notifications": 1_789_000_000,
      "email_notifications": 1_123_000_000,
      "sms_notifications": 987_654_321,
      "live_service_count": random.randrange(1, 1000),
      "notifications_by_type": [
        {
          "date": "2021-02-21",
          "emails": 1_234_567, "sms": 123_456,
        },
        {
          "date": "2021-02-22",
          "emails": 1, "sms": 2,
        },
        {
          "date": "2021-02-23",
          "emails": 1, "sms": 2,
        },
        {
          "date": "2021-02-24",
          "emails": 1, "sms": 2,
        },
        {
          "date": "2021-02-25",
          "emails": 1, "sms": 2,
        },
        {
          "date": "2021-02-26",
          "emails": 1, "sms": 2,
        },
        {
          "date": "2021-02-27",
          "emails": 1, "sms": 2,
        },
      ],
      "processing_time": [
        {
          "date": "2021-02-21",
          "percentage_under_10_seconds": 99.25
        },
        {
          "date": "2021-02-22",
          "percentage_under_10_seconds": 95.30
        },
        {
          "date": "2021-02-23",
          "percentage_under_10_seconds": 95.0
        },
        {
          "date": "2021-02-24",
          "percentage_under_10_seconds": 100.0
        },
        {
          "date": "2021-02-25",
          "percentage_under_10_seconds": 99.99
        },
        {
          "date": "2021-02-26",
          "percentage_under_10_seconds": 100.0
        },
        {
          "date": "2021-02-27",
          "percentage_under_10_seconds": 98.60
        },
      ],
      "services_using_notify": [
        {
          "organisation_id": uuid.uuid4(),
          "organisation_name": "Department of Examples and Patterns",
          "service_id": uuid.uuid4(),
          "service_name": "Example service"
        },
        {
          "organisation_id": uuid.uuid4(),
          "organisation_name": "Department of Examples and Patterns",
          "service_id": uuid.uuid4(),
          "service_name": "Example service 2"
        },
        {
          "organisation_id": uuid.uuid4(),
          "organisation_name": "Department of One Service",
          "service_id": uuid.uuid4(),
          "service_name": "Example service 3"
        },
        {
          # On production there should be no live services without an
          # organisation, but this isn’t always true in people’s local
          # environments
          "organisation_id": None,
          "organisation_name": None,
          "service_id": uuid.uuid4(),
          "service_name": "Example service 4"
        },
      ],
    }


@freeze_time('2021-01-01 12:00')
def test_should_render_performance_page(
    mocker,
    client_request,
    mock_get_service_and_organisation_counts,
):
    mock_get_performance_data = mocker.patch(
        'app.performance_dashboard_api_client.get_performance_dashboard_stats',
        return_value=_get_example_performance_data(),
    )
    page = client_request.get('main.performance')
    mock_get_performance_data.assert_called_once_with(
        start_date=date(2020, 12, 25),
        end_date=date(2021, 1, 1),
    )
    assert normalize_spaces(page.select_one('main').text) == (
        'Performance data '
        ''
        'Messages sent since May 2016 '
        '1.8 billion total '
        '1.1 billion emails '
        '987.7 million text messages '
        ''
        'Messages sent since May 2016 '
        'Date Emails Text messages '
        '26 February 2021 1 2 '
        '25 February 2021 1 2 '
        '24 February 2021 1 2 '
        '23 February 2021 1 2 '
        '22 February 2021 1 2 '
        '21 February 2021 1 2 '
        '20 February 2021 1,234,567 123,456 '


        'Only showing the last 7 days '
        ''
        'Messages sent within 10 seconds '
        '98.31% on average '
        'Messages sent within 10 seconds '
        'Date Percentage '
        '26 February 2021 98.60% '
        '25 February 2021 100.00% '
        '24 February 2021 99.99% '
        '23 February 2021 100.00% '
        '22 February 2021 95.00% '
        '21 February 2021 95.30% '
        '20 February 2021 99.25% '
        'Only showing the last 7 days '
        ''
        'Organisations using Notify '
        'There are 111 organisations and 9,999 services using Notify. '
        'Organisations using Notify '
        'Organisation Number of live services '
        'Department of Examples and Patterns 2 '
        'Department of One Service 1 '
        'No organisation 1'
    )
