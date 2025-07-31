"""Simple tests to verify ZAP security fixes"""
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


def test_cross_origin_embedder_policy_exists(client_request, mocker, mock_get_service_and_organization_counts):
    """Check that Cross-Origin-Embedder-Policy header is present"""
    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()
    response = client_request.get_response('.index')

    assert 'Cross-Origin-Embedder-Policy' in response.headers
    assert response.headers['Cross-Origin-Embedder-Policy'] == 'credentialless'
