from functools import partial

import pytest
from bs4 import BeautifulSoup
from flask import url_for
from freezegun import freeze_time

from tests.conftest import SERVICE_ONE_ID, normalize_spaces, sample_uuid


def test_non_logged_in_user_can_see_homepage(
    client_request,
    mock_get_service_and_organisation_counts,
):
    client_request.logout()
    page = client_request.get('main.index', _test_page_title=False)

    assert page.h1.text.strip() == (
        'Send text messages and email to your users'
    )

    assert page.select_one('a[role=button][draggable=false]')['href'] == url_for(
        'main.register'
    )

    assert page.select_one('meta[name=description]')['content'].strip() == (
        'U.S. Notify lets you send text messages and email '
        'to your users. Try it now if you work in federal, state or local government.'
    )

    assert normalize_spaces(page.select_one('#whos-using-notify').text) == (
        'Who’s using U.S. Notify '
        'There are 111 organizations and 9,999 services using Notify. '
        'See the list of services and organizations.'
    )
    assert page.select_one('#whos-using-notify a')['href'] == url_for(
        'main.performance'
    )


def test_logged_in_user_redirects_to_choose_account(
    client_request,
    api_user_active,
    mock_get_user,
    mock_get_user_by_email,
    mock_login,
):
    client_request.get(
        'main.index',
        _expected_status=302,
    )
    client_request.get(
        'main.sign_in',
        _expected_status=302,
        _expected_redirect=url_for('main.show_accounts_or_dashboard')
    )


def test_robots(client_request):
    client_request.get_url('/robots.txt', _expected_status=404)


@pytest.mark.parametrize('endpoint, kwargs', (
    ('sign_in', {}),
    ('support', {}),
    ('support_public', {}),
    ('triage', {}),
    ('feedback', {'ticket_type': 'ask-question-give-feedback'}),
    ('feedback', {'ticket_type': 'general'}),
    ('feedback', {'ticket_type': 'report-problem'}),
    ('bat_phone', {}),
    ('thanks', {}),
    ('register', {}),
    ('features_email', {}),
    pytest.param('index', {}, marks=pytest.mark.xfail(raises=AssertionError)),
))
@freeze_time('2012-12-12 12:12')  # So we don’t go out of business hours
def test_hiding_pages_from_search_engines(
    client_request,
    mock_get_service_and_organisation_counts,
    endpoint,
    kwargs,
):
    client_request.logout()
    response = client_request.get_response(f'main.{endpoint}', **kwargs)
    assert 'X-Robots-Tag' in response.headers
    assert response.headers['X-Robots-Tag'] == 'noindex'

    page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
    assert page.select_one('meta[name=robots]')['content'] == 'noindex'


@pytest.mark.parametrize('view', [
    'cookies', 'privacy', 'pricing', 'terms', 'roadmap',
    'features', 'documentation', 'security',
    'message_status', 'features_email', 'features_sms',
    'how_to_pay', 'get_started',
    'guidance_index', 'branding_and_customisation',
    'create_and_send_messages', 'edit_and_format_messages',
    'send_files_by_email',
    'billing_details',
])
def test_static_pages(
    client_request,
    mock_get_organisation_by_domain,
    view,
):
    request = partial(client_request.get, 'main.{}'.format(view))

    # Check the page loads when user is signed in
    page = request()
    assert not page.select_one('meta[name=description]')

    # Check it still works when they don’t have a recent service
    with client_request.session_transaction() as session:
        session['service_id'] = None
    request()

    # Check it still works when they sign out
    client_request.logout()
    with client_request.session_transaction() as session:
        session['service_id'] = None
        session['user_id'] = None
    request()


def test_guidance_pages_link_to_service_pages_when_signed_in(
    client_request,
):
    request = partial(client_request.get, 'main.edit_and_format_messages')
    selector = '.list-number li a'

    # Check the page loads when user is signed in
    page = request()
    assert page.select_one(selector)['href'] == url_for(
        'main.choose_template',
        service_id=SERVICE_ONE_ID,
    )

    # Check it still works when they don’t have a recent service
    with client_request.session_transaction() as session:
        session['service_id'] = None
    page = request()
    assert not page.select_one(selector)

    # Check it still works when they sign out
    client_request.logout()
    with client_request.session_transaction() as session:
        session['service_id'] = None
        session['user_id'] = None
    page = request()
    assert not page.select_one(selector)


@pytest.mark.parametrize('view, expected_view', [
    ('information_risk_management', 'security'),
    ('old_integration_testing', 'integration_testing'),
    ('old_roadmap', 'roadmap'),
    ('information_risk_management', 'security'),
    ('old_terms', 'terms'),
    ('information_security', 'using_notify'),
    ('old_using_notify', 'using_notify'),
    ('delivery_and_failure', 'message_status'),
    ('callbacks', 'documentation'),
])
def test_old_static_pages_redirect(
    client_request,
    view,
    expected_view
):
    client_request.logout()
    client_request.get(
        'main.{}'.format(view),
        _expected_status=301,
        _expected_redirect=url_for(
            'main.{}'.format(expected_view),
        ),
    )


def test_message_status_page_contains_message_status_ids(client_request):
    # The 'email-statuses' and 'sms-statuses' id are linked to when we display a message status,
    # so this test ensures we don't accidentally remove them
    page = client_request.get('main.message_status')

    # email-statuses is commented out in view
    # assert page.find(id='email-statuses')
    assert page.find(id='text-message-statuses')


def test_message_status_page_contains_link_to_support(client_request):
    page = client_request.get('main.message_status')
    sms_status_table = page.find(id='text-message-statuses').findNext('tbody')

    temp_fail_details_cell = sms_status_table.select_one('tr:nth-child(4) > td:nth-child(2)')
    assert temp_fail_details_cell.find('a').attrs['href'] == url_for('main.support')


def test_old_using_notify_page(client_request):
    client_request.get('main.using_notify', _expected_status=410)


def test_old_integration_testing_page(
    client_request,
):
    page = client_request.get(
        'main.integration_testing',
        _expected_status=410,
    )
    assert normalize_spaces(page.select_one('.govuk-grid-row').text) == (
        'Integration testing '
        'This information has moved. '
        'Refer to the documentation for the client library you are using.'
    )
    assert page.select_one('.govuk-grid-row a')['href'] == url_for(
        'main.documentation'
    )


def test_terms_page_has_correct_content(client_request):
    terms_page = client_request.get('main.terms')
    assert normalize_spaces(terms_page.select('main p')[0].text) == (
        'These terms apply to your service’s use of U.S. Notify. '
        'You must be the service manager to accept them.'
    )


def test_css_is_served_from_correct_path(client_request):

    page = client_request.get('main.documentation')  # easy static page

    for index, link in enumerate(
        page.select('link[rel=stylesheet]')
    ):
        assert link['href'].startswith([
            'https://static.example.com/stylesheets/main.css?',
            'https://static.example.com/stylesheets/print.css?',
        ][index])


@pytest.mark.skip(reason="Update for TTS")
def test_resources_that_use_asset_path_variable_have_correct_path(client_request):

    page = client_request.get('main.documentation')  # easy static page

    logo_svg_fallback = page.select_one('.govuk-header__logotype-crown-fallback-image')

    assert logo_svg_fallback['src'].startswith('https://static.example.com/images/govuk-logotype-crown.png')


@pytest.mark.parametrize('extra_args, email_branding_retrieved', (
    (
        {},
        False,
    ),
    (
        {'branding_style': '__NONE__'},
        False,
    ),
    (
        {'branding_style': sample_uuid()},
        True,
    ),
))
def test_email_branding_preview(
    client_request,
    mock_get_email_branding,
    extra_args,
    email_branding_retrieved,
):
    page = client_request.get(
        'main.email_template',
        _test_page_title=False,
        **extra_args
    )
    assert page.title.text == 'Email branding preview'
    assert mock_get_email_branding.called is email_branding_retrieved


def test_font_preload(
    client_request,
    mock_get_service_and_organisation_counts,
):
    client_request.logout()
    page = client_request.get('main.index', _test_page_title=False)

    preload_tags = page.select('link[rel=preload][as=font][type="font/woff2"][crossorigin]')

    assert len(preload_tags) == 4, 'Run `npm run build` to copy fonts into app/static/fonts/'

    for element in preload_tags:
        assert element['href'].startswith('https://static.example.com/fonts/')
        assert element['href'].endswith('.woff2')


@pytest.mark.parametrize('current_date, expected_rate', (
    ('2022-05-01', '1.72'),
))
@pytest.mark.skip(reason="Currently hidden for TTS")
def test_sms_price(
    client_request,
    mock_get_service_and_organisation_counts,
    current_date,
    expected_rate,
):
    client_request.logout()

    with freeze_time(current_date):
        home_page = client_request.get('main.index', _test_page_title=False)
        pricing_page = client_request.get('main.pricing')

    assert normalize_spaces(
        home_page.select('.product-page-section')[5].select('.govuk-grid-column-one-half')[1].text
    ) == (
        f'Text messages '
        f'Up to 40,000 free text messages a year, '
        f'then {expected_rate} pence per message'
    )

    assert normalize_spaces(
        pricing_page.select_one('#text-messages + p + p').text
    ) == (
        f'When a service has used its annual allowance, it costs '
        f'{expected_rate} pence (plus VAT) for each text message you '
        f'send.'
    )
