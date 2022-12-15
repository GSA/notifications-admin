from functools import partial

import pytest
from flask import url_for
from freezegun import freeze_time

from tests.conftest import (
    SERVICE_ONE_ID,
    create_active_caseworking_user,
    create_active_user_with_permissions,
    create_notification,
    normalize_spaces,
)


@pytest.mark.parametrize('key_type, notification_status, expected_status', [
    (None, 'created', 'Sending'),
    (None, 'sending', 'Sending'),
    (None, 'delivered', 'Delivered'),
    (None, 'failed', 'Failed'),
    (None, 'temporary-failure', 'Phone not accepting messages right now'),
    (None, 'permanent-failure', 'Not delivered'),
    (None, 'technical-failure', 'Technical failure'),
    ('team', 'delivered', 'Delivered'),
    ('live', 'delivered', 'Delivered'),
    ('test', 'sending', 'Sending (test)'),
    ('test', 'delivered', 'Delivered (test)'),
    ('test', 'permanent-failure', 'Not delivered (test)'),
])
@pytest.mark.parametrize('user', [
    create_active_user_with_permissions(),
    create_active_caseworking_user(),
])
@freeze_time("2016-01-01 11:09:00.061258")
def test_notification_status_page_shows_details(
    client_request,
    mocker,
    mock_has_no_jobs,
    service_one,
    fake_uuid,
    user,
    key_type,
    notification_status,
    expected_status,
):

    mocker.patch('app.user_api_client.get_user', return_value=user)

    notification = create_notification(notification_status=notification_status, key_type=key_type)
    _mock_get_notification = mocker.patch('app.notification_api_client.get_notification', return_value=notification)

    page = client_request.get(
        'main.view_notification',
        service_id=service_one['id'],
        notification_id=fake_uuid
    )

    assert normalize_spaces(page.select('.sms-message-recipient')[0].text) == (
        'To: 07123456789'
    )
    assert normalize_spaces(page.select('.sms-message-wrapper')[0].text) == (
        'service one: hello Jo'
    )
    assert normalize_spaces(page.select('.ajax-block-container p')[0].text) == (
        expected_status
    )

    _mock_get_notification.assert_called_with(
        service_one['id'],
        fake_uuid
    )


@pytest.mark.parametrize('notification_type, notification_status, expected_class', [
    ('sms', 'failed', 'error'),
    ('email', 'failed', 'error'),
    ('sms', 'sent', 'sent-international'),
    ('email', 'sent', None),
    ('sms', 'created', 'default'),
    ('email', 'created', 'default'),
])
@freeze_time("2016-01-01 11:09:00.061258")
def test_notification_status_page_formats_email_and_sms_status_correctly(
    client_request,
    mocker,
    mock_has_no_jobs,
    service_one,
    fake_uuid,
    active_user_with_permissions,
    notification_type,
    notification_status,
    expected_class,
):
    mocker.patch('app.user_api_client.get_user', return_value=active_user_with_permissions)
    notification = create_notification(notification_status=notification_status, template_type=notification_type)
    mocker.patch('app.notification_api_client.get_notification', return_value=notification)

    page = client_request.get(
        'main.view_notification',
        service_id=service_one['id'],
        notification_id=fake_uuid
    )
    assert page.select_one(f'.ajax-block-container p.notification-status.{expected_class}')


@pytest.mark.parametrize('template_redaction_setting, expected_content', [
    (False, 'service one: hello Jo'),
    (True, 'service one: hello hidden'),
])
@freeze_time("2016-01-01 11:09:00.061258")
def test_notification_status_page_respects_redaction(
    client_request,
    mocker,
    service_one,
    fake_uuid,
    template_redaction_setting,
    expected_content,
):

    _mock_get_notification = mocker.patch(
        'app.notification_api_client.get_notification',
        return_value=create_notification(redact_personalisation=template_redaction_setting)
    )

    page = client_request.get(
        'main.view_notification',
        service_id=service_one['id'],
        notification_id=fake_uuid
    )

    assert normalize_spaces(page.select('.sms-message-wrapper')[0].text) == expected_content

    _mock_get_notification.assert_called_with(
        service_one['id'],
        fake_uuid,
    )


@pytest.mark.parametrize('extra_args, expected_back_link', [
    (
        {},
        partial(url_for, 'main.view_notifications', message_type='sms', status='sending,delivered,failed'),
    ),
    (
        {'from_job': 'job_id'},
        partial(url_for, 'main.view_job', job_id='job_id'),
    ),
    (
        {'help': '0'},
        None,
    ),
    (
        {'help': '1'},
        None,
    ),
    (
        {'help': '2'},
        None,
    ),
])
def test_notification_status_shows_expected_back_link(
    client_request,
    mocker,
    mock_get_notification,
    fake_uuid,
    extra_args,
    expected_back_link,
):
    page = client_request.get(
        'main.view_notification',
        service_id=SERVICE_ONE_ID,
        notification_id=fake_uuid,
        **extra_args
    )
    back_link = page.select_one('.govuk-back-link')

    if expected_back_link:
        assert back_link['href'] == expected_back_link(service_id=SERVICE_ONE_ID)
    else:
        assert back_link is None


@pytest.mark.parametrize('time_of_viewing_page, expected_message', (
    ('2012-01-01 06:01', (
        "‘sample template’ was sent by Test User today at 1:01am"
    )),
    ('2012-01-02 06:01', (
        "‘sample template’ was sent by Test User yesterday at 1:01am"
    )),
    ('2012-01-03 06:01', (
        "‘sample template’ was sent by Test User on 1 January at 1:01am"
    )),
    ('2013-01-03 06:01', (
        "‘sample template’ was sent by Test User on 1 January 2012 at 1:01am"
    )),
))
def test_notification_page_doesnt_link_to_template_in_tour(
    mocker,
    client_request,
    fake_uuid,
    mock_get_notification,
    time_of_viewing_page,
    expected_message,
):

    with freeze_time('2012-01-01 06:01'):
        notification = create_notification()
        mocker.patch('app.notification_api_client.get_notification', return_value=notification)

    with freeze_time(time_of_viewing_page):
        page = client_request.get(
            'main.view_notification',
            service_id=SERVICE_ONE_ID,
            notification_id=fake_uuid,
            help=3,
        )

    assert normalize_spaces(page.select('main p:nth-of-type(1)')[0].text) == (
        expected_message
    )
    assert len(page.select('main p:nth-of-type(1) a')) == 0


@pytest.mark.parametrize('notification_type', ['email', 'sms'])
@freeze_time('2016-01-01 15:00')
def test_notification_page_does_not_show_cancel_link_for_sms_or_email_notifications(
    client_request,
    mocker,
    fake_uuid,
    notification_type,
):
    notification = create_notification(template_type=notification_type, notification_status='created')
    mocker.patch('app.notification_api_client.get_notification', return_value=notification)

    page = client_request.get(
        'main.view_notification',
        service_id=SERVICE_ONE_ID,
        notification_id=fake_uuid,
    )

    assert 'Cancel sending this letter' not in normalize_spaces(page.text)


@pytest.mark.parametrize('service_permissions, template_type, link_expected', [
    ([], '', False),
    (['inbound_sms'], 'email', False),
    (['inbound_sms'], 'sms', True),
])
def test_notification_page_has_link_to_send_another_for_sms(
    client_request,
    mocker,
    fake_uuid,
    service_one,
    service_permissions,
    template_type,
    link_expected,
):

    service_one['permissions'] = service_permissions
    notification = create_notification(template_type=template_type)
    mocker.patch('app.notification_api_client.get_notification', return_value=notification)

    page = client_request.get(
        'main.view_notification',
        service_id=SERVICE_ONE_ID,
        notification_id=fake_uuid,
    )

    last_paragraph = page.select('main p')[-1]
    conversation_link = url_for(
        '.conversation',
        service_id=SERVICE_ONE_ID,
        notification_id=fake_uuid,
        _anchor='n{}'.format(fake_uuid),
    )

    if link_expected:
        assert normalize_spaces(last_paragraph.text) == (
            'See all text messages sent to this phone number'
        )
        assert last_paragraph.select_one('a')['href'] == conversation_link
    else:
        assert conversation_link not in str(page.select_one('main'))


@pytest.mark.parametrize('notification_type', ['sms', 'email'])
def test_should_show_reply_to_from_notification(
    mocker,
    fake_uuid,
    notification_type,
    client_request,
):
    notification = create_notification(reply_to_text='reply to info', template_type=notification_type)
    mocker.patch('app.notification_api_client.get_notification', return_value=notification)

    page = client_request.get(
        'main.view_notification',
        service_id=SERVICE_ONE_ID,
        notification_id=fake_uuid,
    )

    assert 'reply to info' in page.text
