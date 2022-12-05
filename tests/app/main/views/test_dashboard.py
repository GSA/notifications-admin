import copy
import json
from datetime import datetime

import pytest
from flask import url_for
from freezegun import freeze_time

from app.main.views.dashboard import (
    aggregate_notifications_stats,
    aggregate_status_types,
    aggregate_template_usage,
    format_monthly_stats_to_list,
    get_dashboard_totals,
    get_tuples_of_financial_years,
)
from tests import (
    organisation_json,
    service_json,
    validate_route_permission,
    validate_route_permission_with_client,
)
from tests.conftest import (
    ORGANISATION_ID,
    SERVICE_ONE_ID,
    create_active_caseworking_user,
    create_active_user_view_permissions,
    normalize_spaces,
)

stub_template_stats = [
    {
        'template_type': 'sms',
        'template_name': 'one',
        'template_id': 'id-1',
        'status': 'created',
        'count': 50,
    },
    {
        'template_type': 'email',
        'template_name': 'two',
        'template_id': 'id-2',
        'status': 'created',
        'count': 100,
    },
    {
        'template_type': 'email',
        'template_name': 'two',
        'template_id': 'id-2',
        'status': 'technical-failure',
        'count': 100,
    },
    {
        'template_type': 'sms',
        'template_name': 'one',
        'template_id': 'id-1',
        'status': 'delivered',
        'count': 50,
    },
]


@pytest.mark.parametrize('user', (
    create_active_user_view_permissions(),
    create_active_caseworking_user(),
))
def test_redirect_from_old_dashboard(
    client_request,
    user,
    mocker,
):
    mocker.patch('app.user_api_client.get_user', return_value=user)
    expected_location = '/services/{}'.format(SERVICE_ONE_ID)

    client_request.get_url(
        '/services/{}/dashboard'.format(SERVICE_ONE_ID),
        _expected_redirect=expected_location,
    )

    assert expected_location == url_for('main.service_dashboard', service_id=SERVICE_ONE_ID)


def test_redirect_caseworkers_to_templates(
    client_request,
    mocker,
    active_caseworking_user,
):
    mocker.patch('app.user_api_client.get_user', return_value=active_caseworking_user)
    client_request.get(
        'main.service_dashboard',
        service_id=SERVICE_ONE_ID,
        _expected_status=302,
        _expected_redirect=url_for(
            'main.choose_template',
            service_id=SERVICE_ONE_ID,
        )
    )


def test_get_started(
    client_request,
    mocker,
    mock_get_service_templates_when_no_templates_exist,
    mock_has_no_jobs,
    mock_get_service_statistics,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    mocker.patch(
        'app.template_statistics_client.get_template_statistics_for_service',
        return_value=copy.deepcopy(stub_template_stats)
    )

    page = client_request.get(
        'main.service_dashboard',
        service_id=SERVICE_ONE_ID,
    )

    mock_get_service_templates_when_no_templates_exist.assert_called_once_with(SERVICE_ONE_ID)
    assert 'Get started' in page.text


def test_get_started_is_hidden_once_templates_exist(
    client_request,
    mocker,
    mock_get_service_templates,
    mock_has_no_jobs,
    mock_get_service_statistics,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    mocker.patch(
        'app.template_statistics_client.get_template_statistics_for_service',
        return_value=copy.deepcopy(stub_template_stats)
    )
    page = client_request.get(
        'main.service_dashboard',
        service_id=SERVICE_ONE_ID,
    )

    mock_get_service_templates.assert_called_once_with(SERVICE_ONE_ID)
    assert not page.find('h2', string='Get started')


def test_inbound_messages_not_visible_to_service_without_permissions(
    client_request,
    mocker,
    service_one,
    mock_get_service_templates_when_no_templates_exist,
    mock_has_no_jobs,
    mock_get_service_statistics,
    mock_get_template_statistics,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):

    service_one['permissions'] = []

    page = client_request.get(
        'main.service_dashboard',
        service_id=SERVICE_ONE_ID,
    )

    assert not page.select('.big-number-meta-wrapper')
    assert mock_get_inbound_sms_summary.called is False


def test_inbound_messages_shows_count_of_messages_when_there_are_messages(
    client_request,
    mocker,
    service_one,
    mock_get_service_templates_when_no_templates_exist,
    mock_get_jobs,
    mock_get_scheduled_job_stats,
    mock_get_service_statistics,
    mock_get_template_statistics,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    service_one['permissions'] = ['inbound_sms']
    page = client_request.get(
        'main.service_dashboard',
        service_id=SERVICE_ONE_ID,
    )
    mock_get_jobs.assert_called_once_with(SERVICE_ONE_ID)
    banner = page.select('a.banner-dashboard')[1]
    assert normalize_spaces(
        banner.text
    ) == '9,999 text messages received latest message just now'
    assert banner['href'] == url_for(
        'main.inbox', service_id=SERVICE_ONE_ID
    )


def test_inbound_messages_shows_count_of_messages_when_there_are_no_messages(
    client_request,
    mocker,
    service_one,
    mock_get_service_templates_when_no_templates_exist,
    mock_get_jobs,
    mock_get_scheduled_job_stats,
    mock_get_service_statistics,
    mock_get_template_statistics,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary_with_no_messages,
):
    service_one['permissions'] = ['inbound_sms']
    page = client_request.get(
        'main.service_dashboard',
        service_id=SERVICE_ONE_ID,
    )
    mock_get_jobs.assert_called_once_with(SERVICE_ONE_ID)
    banner = page.select('a.banner-dashboard')[1]
    assert normalize_spaces(banner.text) == '0 text messages received'
    assert banner['href'] == url_for(
        'main.inbox', service_id=SERVICE_ONE_ID
    )


@pytest.mark.parametrize('index, expected_row', enumerate([
    '07900 900000 message-1 1 hour ago',
    '07900 900000 message-2 1 hour ago',
    '07900 900000 message-3 1 hour ago',
    '07900 900002 message-4 3 hours ago',
    '+33 1 12 34 56 78 message-5 5 hours ago',
    '+1 202-555-0104 message-6 7 hours ago',
    '+1 202-555-0104 message-7 9 hours ago',
    '+682 12345 message-8 9 hours ago',
]))
def test_inbox_showing_inbound_messages(
    client_request,
    service_one,
    mock_get_service_templates_when_no_templates_exist,
    mock_get_service_statistics,
    mock_get_template_statistics,
    mock_get_annual_usage_for_service,
    mock_get_most_recent_inbound_sms,
    index,
    expected_row,
):

    service_one['permissions'] = ['inbound_sms']

    page = client_request.get(
        'main.inbox',
        service_id=SERVICE_ONE_ID,
    )

    rows = page.select('tbody tr')
    assert len(rows) == 8
    assert normalize_spaces(rows[index].text) == expected_row
    assert page.select_one('a[download]')['href'] == url_for(
        'main.inbox_download',
        service_id=SERVICE_ONE_ID,
    )


def test_get_inbound_sms_shows_page_links(
    client_request,
    service_one,
    mock_get_service_templates_when_no_templates_exist,
    mock_get_service_statistics,
    mock_get_template_statistics,
    mock_get_annual_usage_for_service,
    mock_get_most_recent_inbound_sms,
    mock_get_inbound_number_for_service,
):
    service_one['permissions'] = ['inbound_sms']

    page = client_request.get(
        'main.inbox',
        service_id=SERVICE_ONE_ID,
        page=2,
    )

    assert 'Next page' in page.find('li', {'class': 'next-page'}).text
    assert 'Previous page' in page.find('li', {'class': 'previous-page'}).text


def test_empty_inbox(
    client_request,
    service_one,
    mock_get_service_templates_when_no_templates_exist,
    mock_get_service_statistics,
    mock_get_template_statistics,
    mock_get_annual_usage_for_service,
    mock_get_most_recent_inbound_sms_with_no_messages,
    mock_get_inbound_number_for_service,
):

    service_one['permissions'] = ['inbound_sms']

    page = client_request.get(
        'main.inbox',
        service_id=SERVICE_ONE_ID,
    )

    assert normalize_spaces(page.select('tbody tr')) == (
        'When users text your service’s phone number (0781239871) you’ll see the messages here'
    )
    assert not page.select('a[download]')
    assert not page.select('li.next-page')
    assert not page.select('li.previous-page')


@pytest.mark.parametrize('endpoint', [
    'main.inbox',
    'main.inbox_updates',
])
def test_inbox_not_accessible_to_service_without_permissions(
    client_request,
    service_one,
    endpoint,
):
    service_one['permissions'] = []
    client_request.get(
        endpoint,
        service_id=SERVICE_ONE_ID,
        _expected_status=403,
    )


def test_anyone_can_see_inbox(
    client_request,
    api_user_active,
    service_one,
    mocker,
    mock_get_most_recent_inbound_sms_with_no_messages,
    mock_get_inbound_number_for_service,
):

    service_one['permissions'] = ['inbound_sms']

    validate_route_permission_with_client(
        mocker,
        client_request,
        'GET',
        200,
        url_for('main.inbox', service_id=service_one['id']),
        ['view_activity'],
        api_user_active,
        service_one,
    )


def test_view_inbox_updates(
    client_request,
    service_one,
    mocker,
    mock_get_most_recent_inbound_sms_with_no_messages,
):
    service_one['permissions'] += ['inbound_sms']

    mock_get_partials = mocker.patch(
        'app.main.views.dashboard.get_inbox_partials',
        return_value={'messages': 'foo'},
    )

    response = client_request.get_response(
        'main.inbox_updates', service_id=SERVICE_ONE_ID,
    )

    assert json.loads(response.get_data(as_text=True)) == {'messages': 'foo'}

    mock_get_partials.assert_called_once_with(SERVICE_ONE_ID)


@freeze_time("2016-07-01 18:00")
def test_download_inbox(
    client_request,
    mock_get_inbound_sms,
):
    response = client_request.get_response(
        'main.inbox_download',
        service_id=SERVICE_ONE_ID,
    )
    assert response.headers['Content-Type'] == (
        'text/csv; '
        'charset=utf-8'
    )
    assert response.headers['Content-Disposition'] == (
        'inline; '
        'filename="Received text messages 2016-07-01.csv"'
    )
    assert response.get_data(as_text=True) == (
        'Phone number,Message,Received\r\n'
        '07900 900000,message-1,2016-07-01 13:00\r\n'
        '07900 900000,message-2,2016-07-01 12:59\r\n'
        '07900 900000,message-3,2016-07-01 12:59\r\n'
        '07900 900002,message-4,2016-07-01 10:59\r\n'
        '+33 1 12 34 56 78,message-5,2016-07-01 08:59\r\n'
        '+1 202-555-0104,message-6,2016-07-01 06:59\r\n'
        '+1 202-555-0104,message-7,2016-07-01 04:59\r\n'
        '+682 12345,message-8,2016-07-01 04:59\r\n'
    )


@freeze_time("2016-07-01 13:00")
@pytest.mark.parametrize('message_content, expected_cell', [
    ('=2+5', '2+5'),
    ('==2+5', '2+5'),
    ('-2+5', '2+5'),
    ('+2+5', '2+5'),
    ('@2+5', '2+5'),
    ('looks safe,=2+5', '"looks safe,=2+5"'),
])
def test_download_inbox_strips_formulae(
    mocker,
    client_request,
    fake_uuid,
    message_content,
    expected_cell,
):

    mocker.patch(
        'app.service_api_client.get_inbound_sms',
        return_value={
            'has_next': False,
            'data': [{
                'user_number': 'elevenchars',
                'notify_number': 'foo',
                'content': message_content,
                'created_at': datetime.utcnow().isoformat(),
                'id': fake_uuid,
            }]
        },
    )
    response = client_request.get_response(
        'main.inbox_download',
        service_id=SERVICE_ONE_ID,
    )
    assert expected_cell in response.get_data(as_text=True).split('\r\n')[1]


def test_should_show_recent_templates_on_dashboard(
    client_request,
    mocker,
    mock_get_service_templates,
    mock_has_no_jobs,
    mock_get_service_statistics,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    mock_template_stats = mocker.patch('app.template_statistics_client.get_template_statistics_for_service',
                                       return_value=copy.deepcopy(stub_template_stats))

    page = client_request.get(
        'main.service_dashboard',
        service_id=SERVICE_ONE_ID,
    )

    mock_template_stats.assert_called_once_with(SERVICE_ONE_ID, limit_days=7)

    headers = [header.text.strip() for header in page.find_all('h2') + page.find_all('h1')]
    assert 'In the last 7 days' in headers

    table_rows = page.find_all('tbody')[0].find_all('tr')

    assert len(table_rows) == 2

    assert 'two' in table_rows[0].find_all('th')[0].text
    assert 'Email template' in table_rows[0].find_all('th')[0].text
    assert '200' in table_rows[0].find_all('td')[0].text

    assert 'one' in table_rows[1].find_all('th')[0].text
    assert 'Text message template' in table_rows[1].find_all('th')[0].text
    assert '100' in table_rows[1].find_all('td')[0].text


@pytest.mark.parametrize('stats', (
    pytest.param(
        [stub_template_stats[0]],
    ),
    pytest.param(
        [stub_template_stats[0], stub_template_stats[1]],
        marks=pytest.mark.xfail(raises=AssertionError),
    )
))
def test_should_not_show_recent_templates_on_dashboard_if_only_one_template_used(
    client_request,
    mocker,
    mock_get_service_templates,
    mock_has_no_jobs,
    mock_get_service_statistics,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
    stats,
):
    mock_template_stats = mocker.patch(
        'app.template_statistics_client.get_template_statistics_for_service',
        return_value=stats,
    )

    page = client_request.get('main.service_dashboard', service_id=SERVICE_ONE_ID)
    main = page.select_one('main').text

    mock_template_stats.assert_called_once_with(SERVICE_ONE_ID, limit_days=7)

    assert stats[0]['template_name'] == 'one'
    assert stats[0]['template_name'] not in main

    # count appears as total, but not per template
    expected_count = stats[0]['count']
    assert expected_count == 50
    assert normalize_spaces(
        page.select_one('#total-sms .big-number-smaller').text
    ) == (
        '{} text messages sent'.format(expected_count)
    )


@freeze_time("2016-07-01 12:00")  # 4 months into 2016 financial year
@pytest.mark.parametrize('extra_args', [
    {},
    {'year': '2016'},
])
def test_should_show_redirect_from_template_history(
    client_request,
    extra_args,
):
    client_request.get(
        'main.template_history',
        service_id=SERVICE_ONE_ID,
        _expected_status=301,
        **extra_args,
    )


@freeze_time("2017-01-01 12:00")  # 4 months into 2016 financial year
@pytest.mark.parametrize('extra_args', [
    {},
    {'year': '2016'},
])
def test_should_show_monthly_breakdown_of_template_usage(
    client_request,
    mock_get_monthly_template_usage,
    extra_args,
):
    page = client_request.get(
        'main.template_usage',
        service_id=SERVICE_ONE_ID,
        **extra_args
    )

    mock_get_monthly_template_usage.assert_called_once_with(SERVICE_ONE_ID, 2016)

    table_rows = page.select('tbody tr')

    assert ' '.join(table_rows[0].text.split()) == (
        'My first template '
        'Text message template '
        '2'
    )

    assert len(table_rows) == len(['October'])
    assert len(page.select('.table-no-data')) == len(['November', 'December', 'January'])


def test_anyone_can_see_monthly_breakdown(
    client_request,
    api_user_active,
    service_one,
    mocker,
    mock_get_monthly_notification_stats,
):
    validate_route_permission_with_client(
        mocker,
        client_request,
        'GET',
        200,
        url_for('main.monthly', service_id=service_one['id']),
        ['view_activity'],
        api_user_active,
        service_one,
    )


@pytest.mark.parametrize('endpoint', [
    'main.monthly',
    'main.template_usage',
])
@freeze_time("2015-01-01 15:15:15.000000")
def test_stats_pages_show_last_3_years(
    client_request,
    endpoint,
    mock_get_monthly_notification_stats,
    mock_get_monthly_template_usage,
):
    page = client_request.get(
        endpoint,
        service_id=SERVICE_ONE_ID,
    )

    assert normalize_spaces(page.select_one('.pill').text) == (
        '2014 to 2015 fiscal year '
        '2013 to 2014 fiscal year '
        '2012 to 2013 fiscal year'
    )


def test_monthly_has_equal_length_tables(
    client_request,
    service_one,
    mock_get_monthly_notification_stats,
):
    page = client_request.get(
        'main.monthly',
        service_id=service_one['id']
    )

    assert page.select_one('.table-field-headings th').get('width') == "33%"


@freeze_time("2016-01-01 11:09:00.061258")
def test_should_show_upcoming_jobs_on_dashboard(
    client_request,
    mock_get_service_templates,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_get_jobs,
    mock_get_scheduled_job_stats,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    page = client_request.get(
        'main.service_dashboard',
        service_id=SERVICE_ONE_ID,
    )

    mock_get_jobs.assert_called_once_with(SERVICE_ONE_ID)
    mock_get_scheduled_job_stats.assert_called_once_with(SERVICE_ONE_ID)

    assert normalize_spaces(
        page.select_one('main h2').text
    ) == (
        'In the next few days'
    )

    assert normalize_spaces(
        page.select_one('a.banner-dashboard').text
    ) == (
        '2 files waiting to send '
        'sending starts today at 6:09am'
    )

    assert page.select_one('a.banner-dashboard')['href'] == url_for(
        'main.uploads', service_id=SERVICE_ONE_ID
    )


def test_should_not_show_upcoming_jobs_on_dashboard_if_count_is_0(
    mocker,
    client_request,
    mock_get_service_templates,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_has_jobs,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    mocker.patch('app.job_api_client.get_scheduled_job_stats', return_value={
        'count': 0,
        'soonest_scheduled_for': None,
    })
    page = client_request.get(
        'main.service_dashboard',
        service_id=SERVICE_ONE_ID,
    )
    mock_has_jobs.assert_called_once_with(SERVICE_ONE_ID)
    assert 'In the next few days' not in page.select_one('main').text
    assert 'files waiting to send ' not in page.select_one('main').text


def test_should_not_show_upcoming_jobs_on_dashboard_if_service_has_no_jobs(
    mocker,
    client_request,
    mock_get_service_templates,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_has_no_jobs,
    mock_get_scheduled_job_stats,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    page = client_request.get(
        'main.service_dashboard',
        service_id=SERVICE_ONE_ID,
    )
    mock_has_no_jobs.assert_called_once_with(SERVICE_ONE_ID)
    assert mock_get_scheduled_job_stats.called is False
    assert 'In the next few days' not in page.select_one('main').text
    assert 'files waiting to send ' not in page.select_one('main').text


@pytest.mark.parametrize('permissions', (
    ['email', 'sms'],
))
@pytest.mark.parametrize('totals', [
    (
        {
            'email': {'requested': 0, 'delivered': 0, 'failed': 0},
            'sms': {'requested': 99999, 'delivered': 0, 'failed': 0},
        },
    ),
    (
        {
            'email': {'requested': 0, 'delivered': 0, 'failed': 0},
            'sms': {'requested': 0, 'delivered': 0, 'failed': 0},
        },
    ),
])
def test_correct_font_size_for_big_numbers(
    client_request,
    mocker,
    mock_get_service_templates,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_has_no_jobs,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    service_one,
    permissions,
    totals,
):

    service_one['permissions'] = permissions

    mocker.patch(
        'app.main.views.dashboard.get_dashboard_totals',
        return_value=totals
    )

    page = client_request.get(
        'main.service_dashboard',
        service_id=service_one['id'],
    )

    assert (
        len(page.select_one('[data-key=totals]').select('.govuk-grid-column-one-half'))
    ) == (
        len(page.select_one('[data-key=usage]').select('.govuk-grid-column-one-half'))
    ) == (
        len(page.select('.big-number-with-status .big-number-smaller'))
    ) == 2


def test_should_not_show_jobs_on_dashboard_for_users_with_uploads_page(
    client_request,
    service_one,
    mock_get_service_templates,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_get_jobs,
    mock_get_scheduled_job_stats,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    page = client_request.get(
        'main.service_dashboard',
        service_id=SERVICE_ONE_ID,
    )
    mock_get_jobs.assert_called_once_with(SERVICE_ONE_ID)
    for filename in {
        "export 1/1/2016.xls",
        "all email addresses.xlsx",
        "applicants.ods",
        "thisisatest.csv",
    }:
        assert filename not in page.select_one('main').text


@freeze_time("2012-03-31 12:12:12")
def test_usage_page(
    client_request,
    mock_get_annual_usage_for_service,
    mock_get_monthly_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_monthly_notification_stats,
):
    page = client_request.get(
        'main.usage',
        service_id=SERVICE_ONE_ID,
    )

    mock_get_monthly_usage_for_service.assert_called_once_with(SERVICE_ONE_ID, 2011)
    mock_get_annual_usage_for_service.assert_called_once_with(SERVICE_ONE_ID, 2011)
    mock_get_free_sms_fragment_limit.assert_called_with(SERVICE_ONE_ID, 2011)

    nav = page.find('ul', {'class': 'pill'})
    unselected_nav_links = nav.select('a:not(.pill-item--selected)')
    assert normalize_spaces(nav.find('a', {'aria-current': 'page'}).text) == '2011 to 2012 fiscal year'
    assert normalize_spaces(unselected_nav_links[0].text) == '2010 to 2011 fiscal year'
    assert normalize_spaces(unselected_nav_links[1].text) == '2009 to 2010 fiscal year'

    annual_usage = page.find_all('div', {'class': 'govuk-grid-column-one-half'})
    # print(annual_usage)

    # annual stats are shown in two rows, each with three column; email is col 1
    # email_column = normalize_spaces(annual_usage[0].text + annual_usage[2].text)
    # assert 'Emails' in email_column
    # assert '1,000 sent' in email_column

    sms_column = normalize_spaces(annual_usage[0].text + annual_usage[1].text)
    assert 'Text messages' in sms_column
    assert '251,800 sent' in sms_column
    assert '250,000 free allowance' in sms_column
    assert '0 free allowance remaining' in sms_column
    assert '$29.85 spent' not in sms_column
    assert '1,500 at 1.65 pence' in sms_column
    assert '300 at 1.70 pence' in sms_column


@freeze_time("2012-03-31 12:12:12")
def test_usage_page_no_sms_spend(
    mocker,
    client_request,
    mock_get_monthly_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_monthly_notification_stats,
):
    mocker.patch('app.billing_api_client.get_annual_usage_for_service', return_value=[
        {
            "notification_type": "sms",
            "chargeable_units": 1000,
            "charged_units": 0,
            "rate": 0.0165,
            "cost": 0
        }
    ])

    page = client_request.get(
        'main.usage',
        service_id=SERVICE_ONE_ID,
    )

    annual_usage = page.find_all('div', {'class': 'govuk-grid-column-one-half'})
    sms_column = normalize_spaces(annual_usage[0].text + annual_usage[1].text)
    assert 'Text messages' in sms_column
    assert '250,000 free allowance' in sms_column
    assert '249,000 free allowance remaining' in sms_column
    assert '$0.00 spent' not in sms_column
    assert 'pence per message' not in sms_column


@freeze_time("2012-03-31 12:12:12")
def test_usage_page_monthly_breakdown(
    client_request,
    service_one,
    mock_get_annual_usage_for_service,
    mock_get_monthly_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_monthly_notification_stats,
):
    page = client_request.get('main.usage', service_id=SERVICE_ONE_ID)
    monthly_breakdown = normalize_spaces(page.find('table').text)

    assert 'October' in monthly_breakdown
    assert '249,860 free text messages' in monthly_breakdown

    assert 'February' in monthly_breakdown
    assert '$16.40' in monthly_breakdown
    assert '140 free text messages' in monthly_breakdown
    assert '960 text messages at 1.65p' in monthly_breakdown
    assert '33 text messages at 1.70p' in monthly_breakdown

    assert 'March' in monthly_breakdown
    assert '$20.91' in monthly_breakdown
    assert '1,230 text messages at 1.70p' in monthly_breakdown


@pytest.mark.parametrize(
    'now, expected_number_of_months', [
        (freeze_time("2017-03-31 11:09:00.061258"), 6),
        (freeze_time("2017-01-01 11:09:00.061258"), 4)
    ]
)
def test_usage_page_monthly_breakdown_shows_months_so_far(
    client_request,
    service_one,
    mock_get_annual_usage_for_service,
    mock_get_monthly_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_monthly_notification_stats,
    now,
    expected_number_of_months
):
    with now:
        page = client_request.get('main.usage', service_id=SERVICE_ONE_ID)
        rows = page.find('table').find_all('tr', class_='table-row')
        assert len(rows) == expected_number_of_months


def test_usage_page_with_0_free_allowance(
    mocker,
    client_request,
    mock_get_annual_usage_for_service,
    mock_get_monthly_usage_for_service,
    mock_get_monthly_notification_stats,
):
    mocker.patch(
        'app.billing_api_client.get_free_sms_fragment_limit_for_year',
        return_value=0,
    )
    page = client_request.get(
        'main.usage',
        service_id=SERVICE_ONE_ID,
        year=2020,
    )

    annual_usage = page.select('main .govuk-grid-column-one-half')
    sms_column = normalize_spaces(annual_usage[0].text)

    assert '0 free allowance' in sms_column
    assert 'free allowance remaining' not in sms_column


def test_usage_page_with_year_argument(
    client_request,
    mock_get_annual_usage_for_service,
    mock_get_monthly_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_monthly_notification_stats,
):
    client_request.get(
        'main.usage',
        service_id=SERVICE_ONE_ID,
        year=2000,
    )
    mock_get_monthly_usage_for_service.assert_called_once_with(SERVICE_ONE_ID, 2000)
    mock_get_annual_usage_for_service.assert_called_once_with(SERVICE_ONE_ID, 2000)
    mock_get_free_sms_fragment_limit.assert_called_with(SERVICE_ONE_ID, 2000)
    mock_get_monthly_notification_stats.assert_called_with(SERVICE_ONE_ID, 2000)


def test_usage_page_for_invalid_year(
    client_request,
):
    client_request.get(
        'main.usage',
        service_id=SERVICE_ONE_ID,
        year='abcd',
        _expected_status=404,
    )


@freeze_time("2012-03-31 12:12:12")
def test_future_usage_page(
    client_request,
    mock_get_annual_usage_for_service_in_future,
    mock_get_monthly_usage_for_service_in_future,
    mock_get_free_sms_fragment_limit,
    mock_get_monthly_notification_stats
):
    client_request.get(
        'main.usage',
        service_id=SERVICE_ONE_ID,
        year=2014,
    )

    mock_get_monthly_usage_for_service_in_future.assert_called_once_with(SERVICE_ONE_ID, 2014)
    mock_get_annual_usage_for_service_in_future.assert_called_once_with(SERVICE_ONE_ID, 2014)
    mock_get_free_sms_fragment_limit.assert_called_with(SERVICE_ONE_ID, 2014)
    mock_get_monthly_notification_stats.assert_called_with(SERVICE_ONE_ID, 2014)


def _test_dashboard_menu(client_request, mocker, usr, service, permissions):
    usr['permissions'][str(service['id'])] = permissions
    usr['services'] = [service['id']]
    mocker.patch('app.user_api_client.check_verify_code', return_value=(True, ''))
    mocker.patch('app.service_api_client.get_services', return_value={'data': [service]})
    mocker.patch('app.user_api_client.get_user', return_value=usr)
    mocker.patch('app.user_api_client.get_user_by_email', return_value=usr)
    mocker.patch('app.service_api_client.get_service', return_value={'data': service})
    client_request.login(usr)
    return client_request.get('main.service_dashboard', service_id=service['id'])


def test_menu_send_messages(
    client_request,
    mocker,
    notify_admin,
    api_user_active,
    service_one,
    mock_get_service_templates,
    mock_has_no_jobs,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_get_annual_usage_for_service,
    mock_get_inbound_sms_summary,
    mock_get_free_sms_fragment_limit,
):
    service_one['permissions'] = ['email', 'sms']

    page = _test_dashboard_menu(
        client_request,
        mocker,
        api_user_active,
        service_one,
        ['view_activity', 'send_texts', 'send_emails']
    )
    page = str(page)
    assert url_for(
        'main.choose_template',
        service_id=service_one['id'],
    ) in page
    # assert url_for('main.uploads', service_id=service_one['id']) in page
    assert url_for('main.manage_users', service_id=service_one['id']) in page

    assert url_for('main.service_settings', service_id=service_one['id']) not in page
    # assert url_for('main.api_keys', service_id=service_one['id']) not in page
    assert url_for('main.view_providers') not in page


def test_menu_manage_service(
    client_request,
    mocker,
    api_user_active,
    service_one,
    mock_get_service_templates,
    mock_has_no_jobs,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_get_annual_usage_for_service,
    mock_get_inbound_sms_summary,
    mock_get_free_sms_fragment_limit,
):
    page = _test_dashboard_menu(
        client_request,
        mocker,
        api_user_active,
        service_one,
        ['view_activity', 'manage_templates', 'manage_users', 'manage_settings'])
    page = str(page)
    assert url_for(
        'main.choose_template',
        service_id=service_one['id'],
    ) in page
    assert url_for('main.manage_users', service_id=service_one['id']) in page
    assert url_for('main.service_settings', service_id=service_one['id']) in page

    # assert url_for('main.api_keys', service_id=service_one['id']) not in page


def test_menu_manage_api_keys(
    client_request,
    mocker,
    api_user_active,
    service_one,
    mock_get_service_templates,
    mock_has_no_jobs,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_get_annual_usage_for_service,
    mock_get_inbound_sms_summary,
    mock_get_free_sms_fragment_limit,
):
    page = _test_dashboard_menu(
        client_request,
        mocker,
        api_user_active,
        service_one,
        ['view_activity', 'manage_api_keys'])

    page = str(page)

    assert url_for('main.choose_template', service_id=service_one['id'],) in page
    assert url_for('main.manage_users', service_id=service_one['id']) in page
    assert url_for('main.service_settings', service_id=service_one['id']) in page
    assert url_for('main.api_integration', service_id=service_one['id']) in page


def test_menu_all_services_for_platform_admin_user(
    client_request,
    mocker,
    platform_admin_user,
    service_one,
    mock_get_service_templates,
    mock_has_no_jobs,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_get_annual_usage_for_service,
    mock_get_inbound_sms_summary,
    mock_get_free_sms_fragment_limit,
):
    page = _test_dashboard_menu(
        client_request,
        mocker,
        platform_admin_user,
        service_one,
        [])
    page = str(page)
    assert url_for('main.choose_template', service_id=service_one['id']) in page
    assert url_for('main.manage_users', service_id=service_one['id']) in page
    assert url_for('main.service_settings', service_id=service_one['id']) in page
    # assert url_for('main.view_notifications', service_id=service_one['id'], message_type='email') in page
    assert url_for('main.view_notifications', service_id=service_one['id'], message_type='sms') in page
    # assert url_for('main.api_keys', service_id=service_one['id']) not in page


def test_route_for_service_permissions(
    mocker,
    notify_admin,
    api_user_active,
    service_one,
    mock_get_service,
    mock_get_user,
    mock_get_service_templates,
    mock_has_no_jobs,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    with notify_admin.test_request_context():
        validate_route_permission(
            mocker,
            notify_admin,
            "GET",
            200,
            url_for('main.service_dashboard', service_id=service_one['id']),
            ['view_activity'],
            api_user_active,
            service_one)


def test_aggregate_template_stats():
    expected = aggregate_template_usage(copy.deepcopy(stub_template_stats))
    assert len(expected) == 2
    assert expected[0]['template_name'] == 'two'
    assert expected[0]['count'] == 200
    assert expected[0]['template_id'] == 'id-2'
    assert expected[0]['template_type'] == 'email'
    assert expected[1]['template_name'] == 'one'
    assert expected[1]['count'] == 100
    assert expected[1]['template_id'] == 'id-1'
    assert expected[1]['template_type'] == 'sms'


def test_aggregate_notifications_stats():
    expected = aggregate_notifications_stats(copy.deepcopy(stub_template_stats))
    assert expected == {
        "sms": {"requested": 100, "delivered": 50, "failed": 0},
        "email": {"requested": 200, "delivered": 0, "failed": 100}
    }


def test_service_dashboard_updates_gets_dashboard_totals(
    mocker,
    client_request,
    mock_get_service_templates,
    mock_get_template_statistics,
    mock_get_service_statistics,
    mock_has_no_jobs,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_inbound_sms_summary,
):
    mocker.patch('app.main.views.dashboard.get_dashboard_totals', return_value={
        'email': {'requested': 123, 'delivered': 0, 'failed': 0},
        'sms': {'requested': 456, 'delivered': 0, 'failed': 0}
    })

    page = client_request.get(
        'main.service_dashboard',
        service_id=SERVICE_ONE_ID,
    )

    numbers = [number.text.strip() for number in page.find_all('span', class_='big-number-number')]
    # assert '123' in numbers  # email is disabled
    assert '456' in numbers


def test_get_dashboard_totals_adds_percentages():
    stats = {
        'sms': {
            'requested': 3,
            'delivered': 0,
            'failed': 2
        },
        'email': {
            'requested': 0,
            'delivered': 0,
            'failed': 0
        }
    }
    assert get_dashboard_totals(stats)['sms']['failed_percentage'] == '66.7'
    assert get_dashboard_totals(stats)['email']['failed_percentage'] == '0'


@pytest.mark.parametrize(
    'failures,expected', [
        (2, False),
        (3, False),
        (4, True)
    ]
)
def test_get_dashboard_totals_adds_warning(failures, expected):
    stats = {
        'sms': {
            'requested': 100,
            'delivered': 0,
            'failed': failures
        }
    }
    assert get_dashboard_totals(stats)['sms']['show_warning'] == expected


def test_format_monthly_stats_empty_case():
    assert format_monthly_stats_to_list({}) == []


def test_format_monthly_stats_labels_month():
    resp = format_monthly_stats_to_list({'2016-07': {}})
    assert resp[0]['name'] == 'July'


def test_format_monthly_stats_has_stats_with_failure_rate():
    resp = format_monthly_stats_to_list({
        '2016-07': {'sms': _stats(3, 1, 2)}
    })
    assert resp[0]['sms_counts'] == {
        'failed': 2,
        'failed_percentage': '66.7',
        'requested': 3,
        'show_warning': True,
    }


def test_format_monthly_stats_works_for_email():
    resp = format_monthly_stats_to_list({
        '2016-07': {
            'sms': {},
            'email': {},
        }
    })
    assert isinstance(resp[0]['sms_counts'], dict)
    assert isinstance(resp[0]['email_counts'], dict)


def _stats(requested, delivered, failed):
    return {'requested': requested, 'delivered': delivered, 'failed': failed}


@pytest.mark.parametrize('dict_in, expected_failed, expected_requested', [
    (
        {},
        0,
        0
    ),
    (
        {'temporary-failure': 1, 'permanent-failure': 1, 'technical-failure': 1},
        3,
        3,
    ),
    (
        {'created': 1, 'pending': 1, 'sending': 1, 'delivered': 1},
        0,
        4,
    ),
])
def test_aggregate_status_types(dict_in, expected_failed, expected_requested):
    sms_counts = aggregate_status_types({'sms': dict_in})['sms_counts']
    assert sms_counts['failed'] == expected_failed
    assert sms_counts['requested'] == expected_requested


def test_get_tuples_of_financial_years():
    assert list(get_tuples_of_financial_years(
        lambda year: 'http://example.com?year={}'.format(year),
        start=2040,
        end=2041,
    )) == [
        ('fiscal year', 2041, 'http://example.com?year=2041', '2041 to 2042'),
        ('fiscal year', 2040, 'http://example.com?year=2040', '2040 to 2041'),
    ]


def test_get_tuples_of_financial_years_defaults_to_2015():
    assert 2015 in list(get_tuples_of_financial_years(
        lambda year: 'http://example.com?year={}'.format(year),
        end=2040,
    ))[-1]


def test_org_breadcrumbs_do_not_show_if_service_has_no_org(
    client_request,
    mock_get_template_statistics,
    mock_get_service_templates_when_no_templates_exist,
    mock_has_no_jobs,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
):
    page = client_request.get('main.service_dashboard', service_id=SERVICE_ONE_ID)

    assert not page.select('.navigation-organisation-link')


def test_org_breadcrumbs_do_not_show_if_user_is_not_an_org_member(
    mocker,
    mock_get_service_templates_when_no_templates_exist,
    mock_has_no_jobs,
    active_caseworking_user,
    client_request,
    mock_get_template_folders,
    mock_get_api_keys,
):
    # active_caseworking_user is not an org member

    service_one_json = service_json(SERVICE_ONE_ID,
                                    users=[active_caseworking_user['id']],
                                    restricted=False,
                                    organisation_id=ORGANISATION_ID)
    mocker.patch('app.service_api_client.get_service', return_value={'data': service_one_json})

    client_request.login(active_caseworking_user, service=service_one_json)
    page = client_request.get('main.service_dashboard', service_id=SERVICE_ONE_ID, _follow_redirects=True)

    assert not page.select('.navigation-organisation-link')


def test_org_breadcrumbs_show_if_user_is_a_member_of_the_services_org(
    mocker,
    mock_get_template_statistics,
    mock_get_service_templates_when_no_templates_exist,
    mock_has_no_jobs,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    active_user_with_permissions,
    client_request,
):
    # active_user_with_permissions (used by the client_request) is an org member

    service_one_json = service_json(SERVICE_ONE_ID,
                                    users=[active_user_with_permissions['id']],
                                    restricted=False,
                                    organisation_id=ORGANISATION_ID)

    mocker.patch('app.service_api_client.get_service', return_value={'data': service_one_json})
    mocker.patch('app.organisations_client.get_organisation', return_value=organisation_json(
        id_=ORGANISATION_ID,
    ))

    page = client_request.get('main.service_dashboard', service_id=SERVICE_ONE_ID)
    assert page.select_one('.navigation-organisation-link')['href'] == url_for(
        'main.organisation_dashboard',
        org_id=ORGANISATION_ID,
    )


def test_org_breadcrumbs_do_not_show_if_user_is_a_member_of_the_services_org_but_service_is_in_trial_mode(
    mocker,
    mock_get_template_statistics,
    mock_get_service_templates_when_no_templates_exist,
    mock_has_no_jobs,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    active_user_with_permissions,
    client_request,
):
    # active_user_with_permissions (used by the client_request) is an org member

    service_one_json = service_json(SERVICE_ONE_ID,
                                    users=[active_user_with_permissions['id']],
                                    organisation_id=ORGANISATION_ID)

    mocker.patch('app.service_api_client.get_service', return_value={'data': service_one_json})
    mocker.patch('app.models.service.Organisation')

    page = client_request.get('main.service_dashboard', service_id=SERVICE_ONE_ID)

    assert not page.select('.navigation-breadcrumb')


def test_org_breadcrumbs_show_if_user_is_platform_admin(
    mocker,
    mock_get_template_statistics,
    mock_get_service_templates_when_no_templates_exist,
    mock_has_no_jobs,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    platform_admin_user,
    client_request,
):
    service_one_json = service_json(SERVICE_ONE_ID,
                                    users=[platform_admin_user['id']],
                                    organisation_id=ORGANISATION_ID)

    mocker.patch('app.service_api_client.get_service', return_value={'data': service_one_json})
    mocker.patch('app.organisations_client.get_organisation', return_value=organisation_json(
        id_=ORGANISATION_ID,
    ))

    client_request.login(platform_admin_user, service_one_json)
    page = client_request.get('main.service_dashboard', service_id=SERVICE_ONE_ID)

    assert page.select_one('.navigation-organisation-link')['href'] == url_for(
        'main.organisation_dashboard',
        org_id=ORGANISATION_ID,
    )


def test_breadcrumb_shows_if_service_is_suspended(
    mocker,
    mock_get_template_statistics,
    mock_get_service_templates_when_no_templates_exist,
    mock_has_no_jobs,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    active_user_with_permissions,
    client_request,
):
    service_one_json = service_json(
        SERVICE_ONE_ID,
        active=False,
        users=[active_user_with_permissions['id']],
    )

    mocker.patch('app.service_api_client.get_service', return_value={'data': service_one_json})
    page = client_request.get('main.service_dashboard', service_id=SERVICE_ONE_ID)

    assert 'Suspended' in page.select_one('.navigation-service-name').text


@pytest.mark.parametrize('permissions', (
    ['email', 'sms'],
))
def test_service_dashboard_shows_usage(
    client_request,
    service_one,
    mock_get_service_templates,
    mock_get_template_statistics,
    mock_has_no_jobs,
    mock_get_annual_usage_for_service,
    mock_get_free_sms_fragment_limit,
    permissions,
):
    service_one['permissions'] = permissions
    page = client_request.get('main.service_dashboard', service_id=SERVICE_ONE_ID)

    assert normalize_spaces(
        page.select_one('[data-key=usage]').text
    ) == (
        '$29.85 '
        'spent on text messages '
        '0 '
        'email disabled during SMS pilot'
    )


def test_service_dashboard_shows_free_allowance(
    mocker,
    client_request,
    service_one,
    mock_get_service_templates,
    mock_get_template_statistics,
    mock_has_no_jobs,
    mock_get_free_sms_fragment_limit,
):
    mocker.patch('app.billing_api_client.get_annual_usage_for_service', return_value=[
        {
            "notification_type": "sms",
            "chargeable_units": 1000,
            "charged_units": 0,
            "rate": 0.0165,
            "cost": 0
        }
    ])

    page = client_request.get('main.service_dashboard', service_id=SERVICE_ONE_ID)

    usage_text = normalize_spaces(page.select_one('[data-key=usage]').text)
    assert 'spent on text messages' not in usage_text
    assert '249,000 free text messages left' in usage_text
