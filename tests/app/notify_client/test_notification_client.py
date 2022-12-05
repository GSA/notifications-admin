import pytest

from app.notify_client.notification_api_client import NotificationApiClient


@pytest.mark.parametrize("arguments,expected_call", [
    (
        {},
        {'url': '/service/abcd1234/notifications', 'params': {}}
    ),
    (
        {'page': 99},
        {'url': '/service/abcd1234/notifications', 'params': {'page': 99}}
    ),
    (
        {'include_jobs': False},
        {'url': '/service/abcd1234/notifications', 'params': {'include_jobs': False}}
    ),
    (
        {'include_from_test_key': True},
        {'url': '/service/abcd1234/notifications', 'params': {'include_from_test_key': True}}
    ),
    (
        {'page': 48, 'limit_days': 3},
        {'url': '/service/abcd1234/notifications', 'params': {'page': 48, 'limit_days': 3}}
    ),
    (
        {'job_id': 'efgh5678'},
        {'url': '/service/abcd1234/job/efgh5678/notifications', 'params': {}}
    ),
    (
        {'job_id': 'efgh5678', 'page': 48},
        {'url': '/service/abcd1234/job/efgh5678/notifications', 'params': {'page': 48}}
    ),
    (
        {'job_id': 'efgh5678', 'page': 48, 'limit_days': 3},
        {'url': '/service/abcd1234/job/efgh5678/notifications', 'params': {'page': 48}}
    ),
])
def test_client_gets_notifications_for_service_and_job_by_page(mocker, arguments, expected_call):

    mock_get = mocker.patch('app.notify_client.notification_api_client.NotificationApiClient.get')
    NotificationApiClient().get_notifications_for_service('abcd1234', **arguments)
    mock_get.assert_called_once_with(**expected_call)


@pytest.mark.parametrize("arguments,expected_call", [
    (
        {'to': "0793433"},
        {'url': '/service/abcd1234/notifications', 'data': {'to': "0793433"}}
    ),
    (
        {'to': "0793433", 'job_id': 'efgh5678'},
        {'url': '/service/abcd1234/job/efgh5678/notifications', 'data': {'to': "0793433"}}
    ),
    (
        {'to': "0793433", 'page': 99},
        {'url': '/service/abcd1234/notifications', 'data': {'to': "0793433", 'page': 99}}
    ),
    (
        {'to': "0793433", 'limit_days': 3},
        {'url': '/service/abcd1234/notifications', 'data': {'to': "0793433", 'limit_days': 3}}
    ),
    (
        {'to': "0793433", 'job_id': 'efgh5678', 'limit_days': 3},
        {'url': '/service/abcd1234/job/efgh5678/notifications', 'data': {'to': "0793433"}}
    ),
])
def test_client_gets_notifications_for_service_and_job_by_page_posts_for_to(mocker, arguments, expected_call):

    mock_post = mocker.patch('app.notify_client.notification_api_client.NotificationApiClient.post')
    NotificationApiClient().get_notifications_for_service('abcd1234', **arguments)
    mock_post.assert_called_once_with(**expected_call)


def test_send_notification(mocker, client_request, active_user_with_permissions):
    mock_post = mocker.patch('app.notify_client.notification_api_client.NotificationApiClient.post')
    NotificationApiClient().send_notification(
        'foo',
        template_id='bar',
        recipient='07700900001',
        personalisation=None,
        sender_id=None
    )
    mock_post.assert_called_once_with(
        url='/service/foo/send-notification',
        data={
            'template_id': 'bar',
            'to': '07700900001',
            'personalisation': None,
            'created_by': active_user_with_permissions['id']
        }
    )


def test_get_notification(mocker):
    mock_get = mocker.patch('app.notify_client.notification_api_client.NotificationApiClient.get')
    NotificationApiClient().get_notification('foo', 'bar')
    mock_get.assert_called_once_with(
        url='/service/foo/notifications/bar'
    )


def test_get_notification_count_for_job_id(mocker):
    mock_get = mocker.patch('app.notify_client.notification_api_client.NotificationApiClient.get')
    NotificationApiClient().get_notification_count_for_job_id(service_id='foo', job_id='bar')
    mock_get.assert_called_once_with(
        url='/service/foo/job/bar/notification_count',
    )
