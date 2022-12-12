import datetime
import re
import uuid
from functools import partial
from unittest.mock import ANY, call

import pytest
from flask import url_for
from freezegun import freeze_time

from app.main.views.platform_admin import (
    create_global_stats,
    format_stats_by_service,
    get_tech_failure_status_box_data,
    is_over_threshold,
    sum_service_usage,
)
from tests import service_json
from tests.conftest import SERVICE_ONE_ID, SERVICE_TWO_ID, normalize_spaces


@pytest.mark.parametrize('endpoint', [
    'main.platform_admin',
    'main.live_services',
    'main.trial_services',
])
def test_should_redirect_if_not_logged_in(
    client_request,
    endpoint
):
    client_request.logout()
    client_request.get(
        endpoint,
        _expected_redirect=url_for('main.sign_in', next=url_for(endpoint)),
    )


@pytest.mark.parametrize('endpoint', [
    'main.platform_admin',
    'main.platform_admin_splash_page',
    'main.live_services',
    'main.trial_services',
])
def test_should_403_if_not_platform_admin(
    client_request,
    endpoint,
):
    client_request.get(endpoint, _expected_status=403)


@pytest.mark.parametrize('endpoint, expected_services_shown', [
    ('main.live_services', 1),
    ('main.trial_services', 1),
])
def test_should_render_platform_admin_page(
    client_request,
    platform_admin_user,
    mock_get_detailed_services,
    endpoint,
    expected_services_shown
):
    client_request.login(platform_admin_user)
    page = client_request.get(endpoint)
    assert [
        normalize_spaces(column.text)
        for column in page.select('tbody tr')[1].select('td')
    ] == [
        '0 emails sent', '0 text messages sent',
    ]
    mock_get_detailed_services.assert_called_once_with({'detailed': True,
                                                        'include_from_test_key': True,
                                                        'only_active': False})


@pytest.mark.parametrize('endpoint', [
    'main.live_services',
    'main.trial_services',
])
@pytest.mark.parametrize('partial_url_for, inc', [
    (partial(url_for), True),
    (partial(url_for, include_from_test_key='y', start_date='', end_date=''), True),
    (partial(url_for, start_date='', end_date=''), False),
])
def test_live_trial_services_toggle_including_from_test_key(
    partial_url_for,
    client_request,
    platform_admin_user,
    mock_get_detailed_services,
    endpoint,
    inc
):
    client_request.login(platform_admin_user)
    client_request.get_url(partial_url_for(endpoint))
    mock_get_detailed_services.assert_called_once_with({
        'detailed': True,
        'only_active': False,
        'include_from_test_key': inc,
    })


@pytest.mark.parametrize('endpoint', [
    'main.live_services',
    'main.trial_services'
])
def test_live_trial_services_with_date_filter(
    client_request,
    platform_admin_user,
    mock_get_detailed_services,
    endpoint
):
    client_request.login(platform_admin_user)
    page = client_request.get(
        endpoint,
        start_date='2016-12-20',
        end_date='2016-12-28',
    )

    assert 'Platform admin' in page.text
    mock_get_detailed_services.assert_called_once_with({
        'include_from_test_key': False,
        'end_date': datetime.date(2016, 12, 28),
        'start_date': datetime.date(2016, 12, 20),
        'detailed': True,
        'only_active': False,
    })


@pytest.mark.parametrize('endpoint, expected_big_numbers', [
    (
        'main.live_services', (
            '55 emails sent 5 failed – 5.0%',
            '110 text messages sent 10 failed – 5.0%',
        ),
    ),
    (
        'main.trial_services', (
            '6 emails sent 1 failed – 10.0%',
            '11 text messages sent 1 failed – 5.0%',
        ),
    ),
])
def test_should_show_total_on_live_trial_services_pages(
    client_request,
    platform_admin_user,
    mock_get_detailed_services,
    endpoint,
    fake_uuid,
    expected_big_numbers,
):
    services = [
        service_json(fake_uuid, 'My Service 1', [], restricted=False),
        service_json(fake_uuid, 'My Service 2', [], restricted=True),
    ]
    services[0]['statistics'] = create_stats(
        emails_requested=100,
        emails_delivered=50,
        emails_failed=5,
        sms_requested=200,
        sms_delivered=100,
        sms_failed=10,
    )

    services[1]['statistics'] = create_stats(
        emails_requested=10,
        emails_delivered=5,
        emails_failed=1,
        sms_requested=20,
        sms_delivered=10,
        sms_failed=1,
    )

    mock_get_detailed_services.return_value = {'data': services}

    client_request.login(platform_admin_user)
    page = client_request.get(endpoint)

    assert (
        normalize_spaces(page.select('.big-number-with-status')[0].text),
        normalize_spaces(page.select('.big-number-with-status')[1].text),
        # normalize_spaces(page.select('.big-number-with-status')[2].text),
    ) == expected_big_numbers


def test_create_global_stats_sets_failure_rates(fake_uuid):
    services = [
        service_json(fake_uuid, 'a', []),
        service_json(fake_uuid, 'b', [])
    ]
    services[0]['statistics'] = create_stats(
        emails_requested=1,
        emails_delivered=1,
        emails_failed=0,
    )
    services[1]['statistics'] = create_stats(
        emails_requested=2,
        emails_delivered=1,
        emails_failed=1,
    )

    stats = create_global_stats(services)
    assert stats == {
        'email': {
            'delivered': 2,
            'failed': 1,
            'requested': 3,
            'failure_rate': '33.3'
        },
        'sms': {
            'delivered': 0,
            'failed': 0,
            'requested': 0,
            'failure_rate': '0'
        },
    }


def create_stats(
    emails_requested=0,
    emails_delivered=0,
    emails_failed=0,
    sms_requested=0,
    sms_delivered=0,
    sms_failed=0,
):
    return {
        'sms': {
            'requested': sms_requested,
            'delivered': sms_delivered,
            'failed': sms_failed,
        },
        'email': {
            'requested': emails_requested,
            'delivered': emails_delivered,
            'failed': emails_failed,
        },
    }


def test_format_stats_by_service_returns_correct_values(fake_uuid):
    services = [service_json(fake_uuid, 'a', [])]
    services[0]['statistics'] = create_stats(
        emails_requested=10,
        emails_delivered=3,
        emails_failed=5,
        sms_requested=50,
        sms_delivered=7,
        sms_failed=11,
    )

    ret = list(format_stats_by_service(services))
    assert len(ret) == 1

    assert ret[0]['stats']['email']['requested'] == 10
    assert ret[0]['stats']['email']['delivered'] == 3
    assert ret[0]['stats']['email']['failed'] == 5

    assert ret[0]['stats']['sms']['requested'] == 50
    assert ret[0]['stats']['sms']['delivered'] == 7
    assert ret[0]['stats']['sms']['failed'] == 11


@pytest.mark.parametrize('endpoint, restricted, research_mode', [
    ('main.trial_services', True, False),
    ('main.live_services', False, False)
])
def test_should_show_email_and_sms_stats_for_all_service_types(
    endpoint,
    restricted,
    research_mode,
    client_request,
    platform_admin_user,
    mock_get_detailed_services,
    fake_uuid,
):
    services = [service_json(fake_uuid, 'My Service', [], restricted=restricted, research_mode=research_mode)]
    services[0]['statistics'] = create_stats(
        emails_requested=10,
        emails_delivered=3,
        emails_failed=5,
        sms_requested=50,
        sms_delivered=7,
        sms_failed=11
    )

    mock_get_detailed_services.return_value = {'data': services}
    client_request.login(platform_admin_user)
    page = client_request.get(endpoint)

    mock_get_detailed_services.assert_called_once_with({'detailed': True,
                                                        'include_from_test_key': True,
                                                        'only_active': ANY})

    table_body = page.find_all('table')[0].find_all('tbody')[0]
    service_row_group = table_body.find_all('tbody')[0].find_all('tr')
    email_stats = service_row_group[1].select('.big-number-number')[0]
    sms_stats = service_row_group[1].select('.big-number-number')[1]

    assert normalize_spaces(email_stats.text) == '10'
    assert normalize_spaces(sms_stats.text) == '50'


@pytest.mark.parametrize('endpoint, restricted', [
    ('main.live_services', False),
    ('main.trial_services', True)
], ids=['live', 'trial'])
def test_should_show_archived_services_last(
    endpoint,
    client_request,
    platform_admin_user,
    mock_get_detailed_services,
    restricted,
):
    services = [
        service_json(name='C', restricted=restricted, active=False, created_at='2002-02-02 12:00:00'),
        service_json(name='B', restricted=restricted, active=True, created_at='2001-01-01 12:00:00'),
        service_json(name='A', restricted=restricted, active=True, created_at='2003-03-03 12:00:00'),
    ]
    services[0]['statistics'] = create_stats()
    services[1]['statistics'] = create_stats()
    services[2]['statistics'] = create_stats()

    mock_get_detailed_services.return_value = {'data': services}
    client_request.login(platform_admin_user)
    page = client_request.get(endpoint)

    mock_get_detailed_services.assert_called_once_with({'detailed': True,
                                                        'include_from_test_key': True,
                                                        'only_active': ANY})

    table_body = page.find_all('table')[0].find_all('tbody')[0]
    services = [service.tr for service in table_body.find_all('tbody')]
    assert len(services) == 3
    assert normalize_spaces(services[0].td.text) == 'A'
    assert normalize_spaces(services[1].td.text) == 'B'
    assert normalize_spaces(services[2].td.text) == 'C Archived'


@pytest.mark.parametrize('endpoint, restricted, research_mode', [
    ('main.trial_services', True, False),
    ('main.live_services', False, False)
])
def test_should_order_services_by_usage_with_inactive_last(
    endpoint,
    restricted,
    research_mode,
    client_request,
    platform_admin_user,
    mock_get_detailed_services,
    fake_uuid,
):
    services = [
        service_json(fake_uuid, 'My Service 1', [], restricted=restricted, research_mode=research_mode),
        service_json(fake_uuid, 'My Service 2', [], restricted=restricted, research_mode=research_mode),
        service_json(fake_uuid, 'My Service 3', [], restricted=restricted, research_mode=research_mode, active=False)
    ]
    services[0]['statistics'] = create_stats(
        emails_requested=100,
        emails_delivered=25,
        emails_failed=25,
        sms_requested=100,
        sms_delivered=25,
        sms_failed=25
    )

    services[1]['statistics'] = create_stats(
        emails_requested=200,
        emails_delivered=50,
        emails_failed=50,
        sms_requested=200,
        sms_delivered=50,
        sms_failed=50
    )

    services[2]['statistics'] = create_stats(
        emails_requested=200,
        emails_delivered=50,
        emails_failed=50,
        sms_requested=200,
        sms_delivered=50,
        sms_failed=50
    )

    mock_get_detailed_services.return_value = {'data': services}
    client_request.login(platform_admin_user)
    page = client_request.get(endpoint)

    mock_get_detailed_services.assert_called_once_with({'detailed': True,
                                                        'include_from_test_key': True,
                                                        'only_active': ANY})

    table_body = page.find_all('table')[0].find_all('tbody')[0]
    services = [service.tr for service in table_body.find_all('tbody')]
    assert len(services) == 3
    assert normalize_spaces(services[0].td.text) == 'My Service 2'
    assert normalize_spaces(services[1].td.text) == 'My Service 1'
    assert normalize_spaces(services[2].td.text) == 'My Service 3 Archived'


def test_sum_service_usage_is_sum_of_all_activity(fake_uuid):
    service = service_json(fake_uuid, 'My Service 1')
    service['statistics'] = create_stats(
        emails_requested=100,
        emails_delivered=25,
        emails_failed=25,
        sms_requested=100,
        sms_delivered=25,
        sms_failed=25
    )
    assert sum_service_usage(service) == 200


def test_sum_service_usage_with_zeros(fake_uuid):
    service = service_json(fake_uuid, 'My Service 1')
    service['statistics'] = create_stats(
        emails_requested=0,
        emails_delivered=0,
        emails_failed=25,
        sms_requested=0,
        sms_delivered=0,
        sms_failed=0
    )
    assert sum_service_usage(service) == 0


def test_platform_admin_list_complaints(
    client_request,
    platform_admin_user,
    mocker
):
    complaint = {
        'id': str(uuid.uuid4()),
        'notification_id': str(uuid.uuid4()),
        'service_id': str(uuid.uuid4()),
        'service_name': 'Sample service',
        'ses_feedback_id': 'Some ses id',
        'complaint_type': 'abuse',
        'complaint_date': '2018-06-05T13:50:30.012354',
        'created_at': '2018-06-05T13:50:30.012354',
    }
    mock = mocker.patch('app.complaint_api_client.get_all_complaints',
                        return_value={'complaints': [complaint], 'links': {}})

    client_request.login(platform_admin_user)
    page = client_request.get(
        'main.platform_admin_list_complaints'
    )

    assert 'Email complaints' in page.text
    assert mock.called


def test_should_show_complaints_with_next_previous(
    client_request,
    platform_admin_user,
    mocker,
    service_one,
    fake_uuid,
):

    api_response = {
        'complaints': [{'complaint_date': None,
                        'complaint_type': None,
                        'created_at': '2017-12-18T05:00:00.000000Z',
                        'id': fake_uuid,
                        'notification_id': fake_uuid,
                        'service_id': service_one['id'],
                        'service_name': service_one['name'],
                        'ses_feedback_id': 'None'}],
        'links': {'last': '/complaint?page=3', 'next': '/complaint?page=3', 'prev': '/complaint?page=1'}
    }

    mocker.patch('app.complaint_api_client.get_all_complaints', return_value=api_response)

    client_request.login(platform_admin_user)
    page = client_request.get(
        'main.platform_admin_list_complaints',
        page=2,
    )

    next_page_link = page.find('a', {'rel': 'next'})
    prev_page_link = page.find('a', {'rel': 'previous'})
    assert (url_for('main.platform_admin_list_complaints', page=3) in next_page_link['href'])
    assert 'Next page' in next_page_link.text.strip()
    assert 'page 3' in next_page_link.text.strip()
    assert (url_for('main.platform_admin_list_complaints', page=1) in prev_page_link['href'])
    assert 'Previous page' in prev_page_link.text.strip()
    assert 'page 1' in prev_page_link.text.strip()


def test_platform_admin_list_complaints_returns_404_with_invalid_page(
    client_request,
    platform_admin_user,
    mocker,
):

    mocker.patch('app.complaint_api_client.get_all_complaints', return_value={'complaints': [], 'links': {}})

    client_request.login(platform_admin_user)
    client_request.get(
        'main.platform_admin_list_complaints',
        page='invalid',
        _expected_status=404,
    )


@pytest.mark.parametrize('number, total, threshold, result', [
    (0, 0, 0, False),
    (1, 1, 0, True),
    (2, 3, 66, True),
    (2, 3, 67, False),
])
def test_is_over_threshold(number, total, threshold, result):
    assert is_over_threshold(number, total, threshold) is result


def test_get_tech_failure_status_box_data_removes_percentage_data():
    stats = {
        'failures':
            {'permanent-failure': 0, 'technical-failure': 0, 'temporary-failure': 1},
        'test-key': 0,
        'total': 5589
    }
    tech_failure_data = get_tech_failure_status_box_data(stats)

    assert 'percentage' not in tech_failure_data


def test_platform_admin_splash_doesnt_talk_to_api(
    client_request,
    platform_admin_user,
):

    client_request.login(platform_admin_user)

    page = client_request.get('main.platform_admin_splash_page')

    assert page.select_one('main .govuk-body a')['href'] == url_for(
        'main.platform_admin',
    )


def test_platform_admin_with_start_and_end_dates_provided(
    mocker,
    client_request,
    platform_admin_user,
):
    start_date = '2018-01-01'
    end_date = '2018-06-01'
    api_args = {'start_date': datetime.date(2018, 1, 1), 'end_date': datetime.date(2018, 6, 1)}

    mocker.patch('app.main.views.platform_admin.make_columns')
    aggregate_stats_mock = mocker.patch(
        'app.main.views.platform_admin.platform_stats_api_client.get_aggregate_platform_stats')
    complaint_count_mock = mocker.patch('app.main.views.platform_admin.complaint_api_client.get_complaint_count')

    client_request.login(platform_admin_user)
    client_request.get(
        'main.platform_admin', start_date=start_date, end_date=end_date,
    )

    aggregate_stats_mock.assert_called_with(api_args)
    complaint_count_mock.assert_called_with(api_args)


@freeze_time('2018-6-11')
def test_platform_admin_with_only_a_start_date_provided(
    mocker,
    client_request,
    platform_admin_user,
):
    start_date = '2018-01-01'
    api_args = {'start_date': datetime.date(2018, 1, 1), 'end_date': datetime.datetime.utcnow().date()}

    mocker.patch('app.main.views.platform_admin.make_columns')
    aggregate_stats_mock = mocker.patch(
        'app.main.views.platform_admin.platform_stats_api_client.get_aggregate_platform_stats')
    complaint_count_mock = mocker.patch('app.main.views.platform_admin.complaint_api_client.get_complaint_count')

    client_request.login(platform_admin_user)
    client_request.get(
        'main.platform_admin',
        start_date=start_date,
    )

    aggregate_stats_mock.assert_called_with(api_args)
    complaint_count_mock.assert_called_with(api_args)


def test_platform_admin_without_dates_provided(
    mocker,
    client_request,
    platform_admin_user,
):
    api_args = {}

    mocker.patch('app.main.views.platform_admin.make_columns')
    aggregate_stats_mock = mocker.patch(
        'app.main.views.platform_admin.platform_stats_api_client.get_aggregate_platform_stats')
    complaint_count_mock = mocker.patch('app.main.views.platform_admin.complaint_api_client.get_complaint_count')

    client_request.login(platform_admin_user)
    client_request.get('main.platform_admin')

    aggregate_stats_mock.assert_called_with(api_args)
    complaint_count_mock.assert_called_with(api_args)


def test_platform_admin_displays_stats_in_right_boxes_and_with_correct_styling(
    mocker,
    client_request,
    platform_admin_user,
):
    platform_stats = {
        'email': {'failures':
                  {'permanent-failure': 3, 'technical-failure': 0, 'temporary-failure': 0},
                  'test-key': 0,
                  'total': 145},
        'sms': {'failures':
                {'permanent-failure': 0, 'technical-failure': 1, 'temporary-failure': 0},
                'test-key': 5,
                'total': 168},
    }
    mocker.patch('app.main.views.platform_admin.platform_stats_api_client.get_aggregate_platform_stats',
                 return_value=platform_stats)
    mocker.patch('app.main.views.platform_admin.complaint_api_client.get_complaint_count', return_value=15)

    client_request.login(platform_admin_user)
    page = client_request.get('main.platform_admin')

    # Email permanent failure status box - number is correct
    assert '3 permanent failures' in page.find_all(
        'div', class_='govuk-grid-column-one-half'
    )[0].find(string=re.compile('permanent'))
    # Email complaints status box - link exists and number is correct
    assert page.find('a', string='15 complaints')
    # SMS total box - number is correct
    assert page.find_all('span', class_='big-number-number')[1].text.strip() == '168'
    # Test SMS box - number is correct
    assert '5' in page.find_all('div', class_='govuk-grid-column-one-half')[3].text
    # SMS technical failure status box - number is correct and failure class is used
    assert '1 technical failures' in page.find_all('div', class_='govuk-grid-column-one-half')[1].find(
        'div', class_='big-number-status-failing').text


def test_clear_cache_shows_form(
    client_request,
    platform_admin_user,
    mocker,
):
    redis = mocker.patch('app.main.views.platform_admin.redis_client')
    client_request.login(platform_admin_user)

    page = client_request.get('main.clear_cache')

    assert not redis.delete_by_pattern.called
    radios = {el['value'] for el in page.select('input[type=checkbox]')}

    assert radios == {
        'user',
        'service',
        'template',
        'email_branding',
        'organisation',
    }


@pytest.mark.parametrize('model_type, expected_calls, expected_confirmation', (
    ('template', [
        call('service-????????-????-????-????-????????????-templates'),
        call('service-????????-????-????-????-????????????-template-????????-????-????-????-????????????-version-*'),
        call('service-????????-????-????-????-????????????-template-????????-????-????-????-????????????-versions'),
    ], 'Removed 6 objects across 3 key formats for template'),
    (['service', 'organisation'], [
        call('has_jobs-????????-????-????-????-????????????'),
        call('service-????????-????-????-????-????????????'),
        call('service-????????-????-????-????-????????????-templates'),
        call('service-????????-????-????-????-????????????-data-retention'),
        call('service-????????-????-????-????-????????????-template-folders'),
        call('organisations'),
        call('domains'),
        call('live-service-and-organisation-counts'),
        call('organisation-????????-????-????-????-????????????-name'),
    ], 'Removed 18 objects across 9 key formats for service, organisation'),
))
def test_clear_cache_submits_and_tells_you_how_many_things_were_deleted(
    client_request,
    platform_admin_user,
    mocker,
    model_type,
    expected_calls,
    expected_confirmation,
):
    redis = mocker.patch('app.main.views.platform_admin.redis_client')
    redis.delete_by_pattern.return_value = 2
    client_request.login(platform_admin_user)

    page = client_request.post(
        'main.clear_cache',
        _data={'model_type': model_type},
        _expected_status=200
    )

    assert redis.delete_by_pattern.call_args_list == expected_calls

    flash_banner = page.find('div', class_='banner-default')
    assert flash_banner.text.strip() == expected_confirmation


def test_clear_cache_requires_option(
    client_request,
    platform_admin_user,
    mocker,
):
    redis = mocker.patch('app.main.views.platform_admin.redis_client')
    client_request.login(platform_admin_user)

    page = client_request.post('main.clear_cache', _data={}, _expected_status=200)

    assert normalize_spaces(page.find('span', class_='govuk-error-message').text) == 'Error: Select at least one option'
    assert not redis.delete_by_pattern.called


def test_reports_page(
    client_request,
    platform_admin_user,
):
    client_request.login(platform_admin_user)
    page = client_request.get('main.platform_admin_reports')

    assert page.find(
        'a', text="Download live services csv report"
    ).attrs['href'] == '/platform-admin/reports/live-services.csv'

    assert page.find(
        'a', text="Monthly notification statuses for live services"
    ).attrs['href'] == url_for('main.notifications_sent_by_service')


def test_get_live_services_report(
    client_request,
    platform_admin_user,
    mocker,
):

    mocker.patch(
        'app.service_api_client.get_live_services_data',
        return_value={'data': [
            {'service_id': 1, 'service_name': 'jessie the oak tree', 'organisation_name': 'Forest',
                'consent_to_research': True, 'contact_name': 'Forest fairy', 'organisation_type': 'Ecosystem',
                'contact_email': 'forest.fairy@digital.cabinet-office.gov.uk', 'contact_mobile': '+447700900986',
                'live_date': 'Sat, 29 Mar 2014 00:00:00 GMT', 'sms_volume_intent': 100, 'email_volume_intent': 50,
                'sms_totals': 300, 'email_totals': 1200,
                'free_sms_fragment_limit': 100},
            {'service_id': 2, 'service_name': 'james the pine tree', 'organisation_name': 'Forest',
                'consent_to_research': None, 'contact_name': None, 'organisation_type': 'Ecosystem',
                'contact_email': None, 'contact_mobile': None,
                'live_date': None, 'sms_volume_intent': None, 'email_volume_intent': 60,
                'sms_totals': 0, 'email_totals': 0,
                'free_sms_fragment_limit': 200},
        ]}
    )
    client_request.login(platform_admin_user)
    response = client_request.get_response(
        'main.live_services_csv',
    )
    report = response.get_data(as_text=True)
    assert report.strip() == (
        'Service ID,Organisation,Organisation type,Service name,Consent to research,Main contact,Contact email,' +
        'Contact mobile,Live date,SMS volume intent,Email volume intent,SMS sent this year,' +
        'Emails sent this year,Free sms allowance\r\n' +

        '1,Forest,Ecosystem,jessie the oak tree,True,Forest fairy,forest.fairy@digital.cabinet-office.gov.uk,' +
        '+447700900986,29-03-2014,100,50,300,1200,100\r\n' +

        '2,Forest,Ecosystem,james the pine tree,,,,,,,60,0,0,200'
    )


def test_get_notifications_sent_by_service_shows_date_form(
    client_request,
    platform_admin_user,
):
    client_request.login(platform_admin_user)
    page = client_request.get('main.notifications_sent_by_service')

    assert [
        (input['type'], input['name'], input.get('value'))
        for input in page.select('input')
    ] == [
        ('text', 'start_date', None),
        ('text', 'end_date', None),
        ('hidden', 'csrf_token', ANY)
    ]


def test_get_notifications_sent_by_service_validates_form(
    mocker,
    client_request,
    platform_admin_user,
):
    mock_get_stats_from_api = mocker.patch('app.main.views.platform_admin.notification_api_client')

    client_request.login(platform_admin_user)

    page = client_request.post(
        'main.notifications_sent_by_service',
        _expected_status=200,
        _data={'start_date': '', 'end_date': '20190101'}
    )

    errors = page.select('.govuk-error-message')
    assert len(errors) == 2

    for error in errors:
        assert 'Not a valid date value' in error.text

    assert mock_get_stats_from_api.called is False


def test_get_billing_report_when_no_results_for_date(client_request, platform_admin_user, mocker):
    client_request.login(platform_admin_user)

    mocker.patch("app.main.views.platform_admin.billing_api_client.get_data_for_billing_report",
                 return_value=[])

    page = client_request.post('main.get_billing_report',
                               _expected_status=200,
                               _data={'start_date': '2019-01-01', 'end_date': '2019-03-31'})

    error = page.select_one('.banner-dangerous')
    assert normalize_spaces(error.text) == 'No results for dates'


def test_get_billing_report_calls_api_and_download_data(
    client_request,
    platform_admin_user,
    mocker
):
    mocker.patch(
        "app.main.views.platform_admin.billing_api_client.get_data_for_billing_report",
        return_value=[{
            'organisation_id': '7832a1be-a1f0-4f2a-982f-05adfd3d6354',
            'organisation_name': 'Org for a - with sms',
            'service_id': '48e82ac0-c8c4-4e46-8712-c83c35a94006',
            'service_name': 'a - with sms',
            'sms_cost': 0,
            'sms_chargeable_units': 0,
            'purchase_order_number': 'PO1234',
            'contact_names': 'Anne, Marie, Josh',
            'contact_email_addresses': 'billing@example.com, accounts@example.com',
            'billing_reference': 'Notify2020'
        }]
    )

    client_request.login(platform_admin_user)
    response = client_request.post_response(
        'main.get_billing_report',
        _data={'start_date': '2019-01-01', 'end_date': '2019-03-31'},
        _expected_status=200,
    )

    assert response.content_type == 'text/csv; charset=utf-8'
    assert response.headers['Content-Disposition'] == (
        'attachment; filename="Billing Report from {} to {}.csv"'.format('2019-01-01', '2019-03-31')
    )

    assert response.get_data(as_text=True) == (
        'organisation_id,organisation_name,service_id,service_name,sms_cost,sms_chargeable_units,' +
        'purchase_order_number,contact_names,contact_email_addresses,' +
        'billing_reference\r\n' +

        '7832a1be-a1f0-4f2a-982f-05adfd3d6354,' +
        'Org for a - with sms,' +
        '48e82ac0-c8c4-4e46-8712-c83c35a94006,' +
        'a - with sms,' +
        '0,' +
        '0,' +
        'PO1234,"Anne, Marie, Josh","billing@example.com, accounts@example.com",Notify2020' +

        '\r\n'
    )


def test_get_notifications_sent_by_service_calls_api_and_downloads_data(
    mocker,
    client_request,
    platform_admin_user,
    service_one,
    service_two,
):
    api_data = [
        ['2019-01-01', SERVICE_ONE_ID, service_one['name'], 'email', 191, 0, 0, 14, 0, 0],
        ['2019-01-01', SERVICE_ONE_ID, service_one['name'], 'sms', 42, 0, 0, 8, 0, 0],
        ['2019-01-01', SERVICE_TWO_ID, service_two['name'], 'email', 3, 1, 0, 2, 0, 0],
    ]
    mocker.patch('app.main.views.platform_admin.notification_api_client.get_notification_status_by_service',
                 return_value=api_data)
    start_date = datetime.date(2019, 1, 1)
    end_date = datetime.date(2019, 1, 31)

    client_request.login(platform_admin_user)
    response = client_request.post_response(
        'main.notifications_sent_by_service',
        _data={'start_date': start_date, 'end_date': end_date},
        _expected_status=200,
    )

    assert response.content_type == 'text/csv; charset=utf-8'
    assert response.headers['Content-Disposition'] == (
        'attachment; filename="{} to {} notification status per service report.csv"'.format(start_date, end_date)
    )
    assert response.get_data(as_text=True) == (
        'date_created,service_id,service_name,notification_type,count_sending,count_delivered,' +
        'count_technical_failure,count_temporary_failure,count_permanent_failure,count_sent\r\n' +

        '2019-01-01,596364a0-858e-42c8-9062-a8fe822260eb,service one,email,191,0,0,14,0,0\r\n' +
        '2019-01-01,596364a0-858e-42c8-9062-a8fe822260eb,service one,sms,42,0,0,8,0,0\r\n' +
        '2019-01-01,147ad62a-2951-4fa1-9ca0-093cd1a52c52,service two,email,3,1,0,2,0,0\r\n'
    )


def test_get_volumes_by_service_report_calls_api_and_download_data(
    client_request,
    platform_admin_user,
    mocker
):
    mocker.patch(
        "app.main.views.platform_admin.billing_api_client.get_data_for_volumes_by_service_report",
        return_value=[{
            "organisation_id": "7832a1be-a1f0-4f2a-982f-05adfd3d6354",
            "organisation_name": "Org name",
            "service_id": "48e82ac0-c8c4-4e46-8712-c83c35a94006",
            "service_name": "service name",
            "free_allowance": 10000,
            "sms_notifications": 10,
            "sms_chargeable_units": 20,
            "email_totals": 8,
        }]
    )

    client_request.login(platform_admin_user)
    response = client_request.post_response(
        'main.get_volumes_by_service',
        _data={'start_date': '2019-01-01', 'end_date': '2019-03-31'},
        _expected_status=200,
    )

    assert response.content_type == 'text/csv; charset=utf-8'
    assert response.headers['Content-Disposition'] == (
        'attachment; filename="Volumes by service report from {} to {}.csv"'.format('2019-01-01', '2019-03-31')
    )

    assert response.get_data(as_text=True) == (
        "organisation id,organisation name,service id,service name,free allowance,sms notifications," +
        "sms chargeable units,email totals\r\n" +

        '7832a1be-a1f0-4f2a-982f-05adfd3d6354,' +
        'Org name,' +
        '48e82ac0-c8c4-4e46-8712-c83c35a94006,' +
        'service name,' +
        '10000,' +
        '10,' +
        '20,' +
        '8' +

        '\r\n'
    )


def test_get_daily_volumes_report_calls_api_and_download_data(
    client_request,
    platform_admin_user,
    mocker
):
    mocker.patch(
        "app.main.views.platform_admin.billing_api_client.get_data_for_daily_volumes_report",
        return_value=[{
            "day": '2019-01-01',
            "sms_totals": 20,
            "sms_fragment_totals": 40,
            "sms_chargeable_units": 60,
            "email_totals": 100,
        }]
    )

    client_request.login(platform_admin_user)
    response = client_request.post_response(
        'main.get_daily_volumes',
        _data={'start_date': '2019-01-01', 'end_date': '2019-03-31'},
        _expected_status=200,
    )

    assert response.content_type == 'text/csv; charset=utf-8'
    assert response.headers['Content-Disposition'] == (
        'attachment; filename="Daily volumes report from {} to {}.csv"'.format('2019-01-01', '2019-03-31')
    )

    assert response.get_data(as_text=True) == (
        "day,sms totals,sms fragment totals,sms chargeable units,email totals\r\n" +

        '2019-01-01,' +
        '20,' +
        '40,' +
        '60,' +
        '100' +

        '\r\n'
    )


def test_get_daily_sms_provider_volumes_report_calls_api_and_download_data(
    client_request,
    platform_admin_user,
    mocker
):
    mocker.patch(
        "app.main.views.platform_admin.billing_api_client.get_data_for_daily_sms_provider_volumes_report",
        return_value=[{
            "day": '2019-01-01',
            "provider": 'foo',
            "sms_totals": 20,
            "sms_fragment_totals": 40,
            "sms_chargeable_units": 60,
            "sms_cost": 80,
        }]
    )

    client_request.login(platform_admin_user)
    response = client_request.post_response(
        'main.get_daily_sms_provider_volumes',
        _data={'start_date': '2019-01-01', 'end_date': '2019-03-31'},
        _expected_status=200,
    )

    assert response.content_type == 'text/csv; charset=utf-8'
    assert response.headers['Content-Disposition'] == (
        'attachment; filename="Daily SMS provider volumes report from {} to {}.csv"'.format('2019-01-01', '2019-03-31')
    )

    assert response.get_data(as_text=True) == (
        "day,provider,sms totals,sms fragment totals,sms chargeable units,sms cost\r\n" +

        '2019-01-01,' +
        'foo,' +
        '20,' +
        '40,' +
        '60,' +
        '80' +

        '\r\n'
    )
