from functools import partial

import pytest
from flask import url_for

letters_urls = [
    partial(url_for, 'main.add_service_template', template_type='letter'),
]


@pytest.mark.parametrize('url', letters_urls)
@pytest.mark.parametrize('permissions, response_code', [
    (['letter'], 200),
    ([], 403)
])
def test_letters_access_restricted(
    client_request,
    platform_admin_user,
    mocker,
    permissions,
    response_code,
    mock_get_service_templates,
    url,
    service_one,
):
    service_one['permissions'] = permissions
    client_request.login(platform_admin_user)
    client_request.get_url(
        url(service_id=service_one['id']),
        _follow_redirects=True,
        _expected_status=response_code,
    )


@pytest.mark.parametrize('url', letters_urls)
def test_letters_lets_in_without_permission(
    client_request,
    mocker,
    mock_login,
    mock_has_permissions,
    api_user_active,
    mock_get_service_templates,
    url,
    service_one
):
    service_one['permissions'] = ['letter']
    mocker.patch('app.service_api_client.get_service', return_value={"data": service_one})

    client_request.login(api_user_active)
    client_request.get_url(url(service_id=service_one['id']))

    assert api_user_active['permissions'] == {}
