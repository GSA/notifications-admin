import json
from datetime import datetime, timezone

import pytest
from flask import url_for
from freezegun import freeze_time

from app.main.views.jobs import get_time_left
from tests import job_json, sample_uuid, user_json
from tests.conftest import (
    SERVICE_ONE_ID,
    create_active_caseworking_user,
    create_active_user_with_permissions,
    normalize_spaces,
)


def test_old_jobs_hub_redirects(
    client_request,
):
    client_request.get(
        'main.view_jobs',
        service_id=SERVICE_ONE_ID,
        _expected_status=302,
        _expected_redirect=url_for(
            'main.uploads',
            service_id=SERVICE_ONE_ID,
        )
    )


@pytest.mark.parametrize('user', [
    create_active_user_with_permissions(),
    create_active_caseworking_user(),
])
@pytest.mark.parametrize(
    "status_argument, expected_api_call", [
        (
            '',
            [
                'created', 'pending', 'sending', 'delivered', 'sent', 'failed',
                'temporary-failure', 'permanent-failure', 'technical-failure',
                'validation-failed'
            ]
        ),
        (
            'sending',
            ['sending', 'created', 'pending']
        ),
        (
            'delivered',
            ['delivered', 'sent']
        ),
        (
            'failed',
            [
                'failed', 'temporary-failure', 'permanent-failure', 'technical-failure',
                'validation-failed'
            ]
        )
    ]
)
@freeze_time("2016-01-01 16:09:00.061258")
def test_should_show_page_for_one_job(
    client_request,
    mock_get_service_template,
    mock_get_job,
    mocker,
    mock_get_notifications,
    mock_get_service_data_retention,
    fake_uuid,
    status_argument,
    expected_api_call,
    user,
):

    page = client_request.get(
        'main.view_job',
        service_id=SERVICE_ONE_ID,
        job_id=fake_uuid,
        status=status_argument
    )

    assert page.h1.text.strip() == 'thisisatest.csv'
    assert ' '.join(page.find('tbody').find('tr').text.split()) == (
        '07123456789 template content Delivered 1 January at 11:10am'
    )
    assert page.find('div', {'data-key': 'notifications'})['data-resource'] == url_for(
        'main.view_job_updates',
        service_id=SERVICE_ONE_ID,
        job_id=fake_uuid,
        status=status_argument,
    )
    csv_link = page.select_one('a[download]')
    assert csv_link['href'] == url_for(
        'main.view_job_csv',
        service_id=SERVICE_ONE_ID,
        job_id=fake_uuid,
        status=status_argument
    )
    assert csv_link.text == 'Download this report (CSV)'
    assert page.find('span', {'id': 'time-left'}).text == 'Data available for 7 days'

    assert normalize_spaces(page.select_one('tbody tr').text) == normalize_spaces(
        '07123456789 '
        'template content '
        'Delivered 1 January at 11:10am'
    )
    assert page.select_one('tbody tr a')['href'] == url_for(
        'main.view_notification',
        service_id=SERVICE_ONE_ID,
        notification_id=sample_uuid(),
        from_job=fake_uuid,
    )

    mock_get_notifications.assert_called_with(
        SERVICE_ONE_ID,
        fake_uuid,
        status=expected_api_call
    )


@freeze_time("2016-01-01 11:09:00.061258")
def test_should_show_page_for_one_job_with_flexible_data_retention(
    client_request,
    active_user_with_permissions,
    mock_get_service_template,
    mock_get_job,
    mocker,
    mock_get_notifications,
    mock_get_service_data_retention,
    fake_uuid,
):

    mock_get_service_data_retention.side_effect = [[{"days_of_retention": 10, "notification_type": "sms"}]]
    page = client_request.get(
        'main.view_job',
        service_id=SERVICE_ONE_ID,
        job_id=fake_uuid,
        status='delivered'
    )

    assert page.find('span', {'id': 'time-left'}).text == 'Data available for 10 days'
    assert "Cancel sending these letters" not in page


def test_get_jobs_should_tell_user_if_more_than_one_page(
    client_request,
    fake_uuid,
    service_one,
    mock_get_job,
    mock_get_service_template,
    mock_get_notifications_with_previous_next,
    mock_get_service_data_retention,
):
    page = client_request.get(
        'main.view_job',
        service_id=service_one['id'],
        job_id=fake_uuid,
        status='',
    )
    assert page.find('p', {'class': 'table-show-more-link'}).text.strip() == 'Only showing the first 50 rows'


def test_should_show_job_in_progress(
    client_request,
    service_one,
    active_user_with_permissions,
    mock_get_service_template,
    mock_get_job_in_progress,
    mocker,
    mock_get_notifications,
    mock_get_service_data_retention,
    fake_uuid,
):
    page = client_request.get(
        'main.view_job',
        service_id=service_one['id'],
        job_id=fake_uuid,
    )
    assert [
        normalize_spaces(link.text)
        for link in page.select('.pill a:not(.pill-item--selected)')
    ] == [
        '10 sending text messages', '0 delivered text messages', '0 failed text messages'
    ]
    assert page.select_one('p.hint').text.strip() == 'Report is 50% complete…'


def test_should_show_job_without_notifications(
    client_request,
    service_one,
    active_user_with_permissions,
    mock_get_service_template,
    mock_get_job_in_progress,
    mocker,
    mock_get_notifications_with_no_notifications,
    mock_get_service_data_retention,
    fake_uuid,
):
    page = client_request.get(
        'main.view_job',
        service_id=service_one['id'],
        job_id=fake_uuid,
    )
    assert [
        normalize_spaces(link.text)
        for link in page.select('.pill a:not(.pill-item--selected)')
    ] == [
        '10 sending text messages', '0 delivered text messages', '0 failed text messages'
    ]
    assert page.select_one('p.hint').text.strip() == 'Report is 50% complete…'
    assert page.select_one('tbody').text.strip() == 'No messages to show yet…'


def test_should_show_job_with_sending_limit_exceeded_status(
    client_request,
    service_one,
    active_user_with_permissions,
    mock_get_service_template,
    mock_get_job_with_sending_limits_exceeded,
    mock_get_notifications_with_no_notifications,
    mock_get_service_data_retention,
    fake_uuid,
):
    page = client_request.get(
        'main.view_job',
        service_id=service_one['id'],
        job_id=fake_uuid,
    )

    assert normalize_spaces(page.select('main p')[1].text) == (
        "Notify cannot send these messages because you have reached your daily limit. You can only send 1,000 messages per day."  # noqa
    )
    assert normalize_spaces(page.select('main p')[2].text) == (
        "Upload this spreadsheet again tomorrow or contact the U.S. Notify team to raise the limit."
    )


@freeze_time("2020-01-10 1:0:0")
@pytest.mark.parametrize('created_at, processing_started, expected_message', (
    # Recently created, not yet started
    (datetime(2020, 1, 10, 0, 0, 0), None, (
        'No messages to show yet…'
    )),
    # Just started
    (datetime(2020, 1, 10, 0, 0, 0), datetime(2020, 1, 10, 0, 0, 1), (
        'No messages to show yet…'
    )),
    # Created a while ago, just started
    (datetime(2020, 1, 1, 0, 0, 0), datetime(2020, 1, 10, 0, 0, 1), (
        'No messages to show yet…'
    )),
    # Created a while ago, started just within the last 24h
    (datetime(2020, 1, 1, 0, 0, 0), datetime(2020, 1, 9, 6, 0, 1), (
        'No messages to show yet…'
    )),
    # Created a while ago, started exactly 24h ago
    # ---
    # It doesn’t matter that 24h (1 day) and 7 days (the service’s data
    # retention) don’t match up. We’re testing the case of no
    # notifications existing more than 1 day after the job started
    # processing. In this case we assume it’s because the service’s
    # data retention has kicked in.
    (datetime(2020, 1, 1, 0, 0, 0), datetime(2020, 1, 9, 1, 0, 0), (
        'These messages have been deleted because they were sent more than 7 days ago'
    )),
))
def test_should_show_old_job(
    client_request,
    service_one,
    active_user_with_permissions,
    mock_get_service_template,
    mocker,
    mock_get_notifications_with_no_notifications,
    mock_get_service_data_retention,
    fake_uuid,
    created_at,
    processing_started,
    expected_message,
):
    mocker.patch('app.job_api_client.get_job', return_value={
        "data": job_json(
            SERVICE_ONE_ID,
            active_user_with_permissions,
            created_at=created_at.replace(tzinfo=timezone.utc).isoformat(),
            processing_started=(
                processing_started.replace(tzinfo=timezone.utc).isoformat()
                if processing_started else None
            ),
        ),
    })
    page = client_request.get(
        'main.view_job',
        service_id=SERVICE_ONE_ID,
        job_id=fake_uuid,
    )
    assert not page.select('.pill')
    assert not page.select('p.hint')
    assert not page.select('a[download]')
    assert page.select_one('tbody').text.strip() == expected_message
    assert [
        normalize_spaces(column.text)
        for column in page.select('main .govuk-grid-column-one-quarter')
    ] == [
        '1 total text messages',
        '1 sending text message',
        '0 delivered text messages',
        '0 failed text messages',
    ]


@freeze_time("2016-01-01T05:00:00.061258")
def test_should_show_scheduled_job(
    client_request,
    mock_get_service_template,
    mock_get_scheduled_job,
    mock_get_service_data_retention,
    mock_get_notifications,
    fake_uuid,
):
    page = client_request.get(
        'main.view_job',
        service_id=SERVICE_ONE_ID,
        job_id=fake_uuid,
    )

    assert normalize_spaces(page.select('main p')[1].text) == (
        'Sending Two week reminder today at midnight'
    )
    assert page.select('main p a')[0]['href'] == url_for(
        'main.view_template_version',
        service_id=SERVICE_ONE_ID,
        template_id='5d729fbd-239c-44ab-b498-75a985f3198f',
        version=1,
    )
    assert page.select_one('main button[type=submit]').text.strip() == 'Cancel sending'


def test_should_cancel_job(
    client_request,
    fake_uuid,
    mock_get_job,
    mock_get_service_template,
    mocker,
):
    mock_cancel = mocker.patch('app.job_api_client.cancel_job')
    client_request.post(
        'main.cancel_job',
        service_id=SERVICE_ONE_ID,
        job_id=fake_uuid,
        _expected_status=302,
        _expected_redirect=url_for(
            'main.service_dashboard',
            service_id=SERVICE_ONE_ID,
        )
    )

    mock_cancel.assert_called_once_with(SERVICE_ONE_ID, fake_uuid)


def test_should_not_show_cancelled_job(
    client_request,
    active_user_with_permissions,
    mock_get_cancelled_job,
    fake_uuid,
):
    client_request.get(
        'main.view_job',
        service_id=SERVICE_ONE_ID,
        job_id=fake_uuid,
        _expected_status=404,
    )


@freeze_time("2016-01-01 05:00:00.000001")
def test_should_show_updates_for_one_job_as_json(
    client_request,
    service_one,
    active_user_with_permissions,
    mock_get_notifications,
    mock_get_service_template,
    mock_get_job,
    mock_get_service_data_retention,
    mocker,
    fake_uuid,
):
    response = client_request.get_response(
        'main.view_job_updates',
        service_id=service_one['id'],
        job_id=fake_uuid,
    )

    content = json.loads(response.get_data(as_text=True))
    assert 'sending' in content['counts']
    assert 'delivered' in content['counts']
    assert 'failed' in content['counts']
    assert 'Recipient' in content['notifications']
    assert '07123456789' in content['notifications']
    assert 'Status' in content['notifications']
    assert 'Delivered' in content['notifications']
    assert '12:01am' in content['notifications']
    assert 'Sent by Test User on 1 January at midnight' in content['status']


@freeze_time("2016-01-01 05:00:00.000001")
def test_should_show_updates_for_scheduled_job_as_json(
    client_request,
    service_one,
    active_user_with_permissions,
    mock_get_notifications,
    mock_get_service_template,
    mock_get_service_data_retention,
    mocker,
    fake_uuid,
):
    mocker.patch('app.job_api_client.get_job', return_value={'data': job_json(
        service_one['id'],
        created_by=user_json(),
        job_id=fake_uuid,
        scheduled_for='2016-06-01T18:00:00+00:00',
        processing_started='2016-06-01T20:00:00+00:00',
    )})

    response = client_request.get_response(
        'main.view_job_updates',
        service_id=service_one['id'],
        job_id=fake_uuid,
    )

    content = response.json
    assert 'sending' in content['counts']
    assert 'delivered' in content['counts']
    assert 'failed' in content['counts']
    assert 'Recipient' in content['notifications']
    assert '07123456789' in content['notifications']
    assert 'Status' in content['notifications']
    assert 'Delivered' in content['notifications']
    assert '12:01am' in content['notifications']
    assert 'Sent by Test User on 1 June at 4:00pm' in content['status']


@pytest.mark.parametrize(
    "job_created_at, expected_message", [
        ("2016-01-10 11:09:00.000000+00:00", "Data available for 7 days"),
        ("2016-01-04 11:09:00.000000+00:00", "Data available for 1 day"),
        ("2016-01-03 11:09:00.000000+00:00", "Data available for 12 hours"),
        ("2016-01-02 23:59:59.000000+00:00", "Data no longer available")
    ]
)
@freeze_time("2016-01-10 12:00:00.000000")
def test_time_left(job_created_at, expected_message):
    assert get_time_left(job_created_at) == expected_message
