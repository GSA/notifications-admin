from app.notify_client.status_api_client import StatusApiClient


def test_get_count_of_live_services_and_organizations(mocker):
    mocker.patch('app.extensions.RedisClient.get', return_value=None)
    client = StatusApiClient()
    mock = mocker.patch.object(client, 'get', return_value={})

    client.get_count_of_live_services_and_organizations()

    mock.assert_called_once_with(url='/_status/live-service-and-organization-counts')


def test_sets_value_in_cache(mocker):
    client = StatusApiClient()

    mock_redis_get = mocker.patch(
        'app.extensions.RedisClient.get',
        return_value=None
    )
    mock_api_get = mocker.patch(
        'app.notify_client.NotifyAdminAPIClient.get',
        return_value={'data_from': 'api'},
    )
    mock_redis_set = mocker.patch(
        'app.extensions.RedisClient.set',
    )

    assert client.get_count_of_live_services_and_organizations() == {'data_from': 'api'}

    mock_redis_get.assert_called_once_with('live-service-and-organization-counts')
    mock_api_get.assert_called_once_with(url='/_status/live-service-and-organization-counts')
    mock_redis_set.assert_called_once_with(
        'live-service-and-organization-counts',
        '{"data_from": "api"}',
        ex=3600
    )


def test_returns_value_from_cache(mocker):
    client = StatusApiClient()

    mock_redis_get = mocker.patch(
        'app.extensions.RedisClient.get',
        return_value=b'{"data_from": "cache"}',
    )
    mock_api_get = mocker.patch(
        'app.notify_client.NotifyAdminAPIClient.get',
    )
    mock_redis_set = mocker.patch(
        'app.extensions.RedisClient.set',
    )

    assert client.get_count_of_live_services_and_organizations() == {'data_from': 'cache'}

    mock_redis_get.assert_called_once_with('live-service-and-organization-counts')

    assert mock_api_get.called is False
    assert mock_redis_set.called is False
