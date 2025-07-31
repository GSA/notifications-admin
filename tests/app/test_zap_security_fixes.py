import pytest


def test_csp_no_unsafe_eval(client_request, mocker, mock_get_service_and_organization_counts):
    """Check that unsafe-eval was removed from CSP"""
    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()
    response = client_request.get_response('.index')
    csp = response.headers.get('Content-Security-Policy', '')

    assert "'unsafe-eval'" not in csp


def test_no_duplicate_form_action(client_request, mocker, mock_get_service_and_organization_counts):
    """Check that form-action only appears once in CSP"""
    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()
    response = client_request.get_response('.index')
    csp = response.headers.get('Content-Security-Policy', '')

    # Count how many times form-action appears
    count = csp.count('form-action')
    assert count == 1


def test_cross_origin_embedder_policy_set_to_credentialless(client_request, mocker, mock_get_service_and_organization_counts):
    """Check that Cross-Origin-Embedder-Policy is set to 'credentialless' for YouTube compatibility"""
    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()
    response = client_request.get_response('.index')

    assert response.headers.get('Cross-Origin-Embedder-Policy') == 'credentialless'


def test_permissions_policy_allows_youtube_features(client_request, mocker, mock_get_service_and_organization_counts):
    """Check that Permissions-Policy allows necessary features for YouTube embeds"""
    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()
    response = client_request.get_response('.index')

    permissions_policy = response.headers.get('Permissions-Policy', '')

    assert 'accelerometer=(self "https://www.youtube-nocookie.com")' in permissions_policy
    assert 'autoplay=(self "https://www.youtube-nocookie.com")' in permissions_policy
    assert 'gyroscope=(self "https://www.youtube-nocookie.com")' in permissions_policy
