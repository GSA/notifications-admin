

def test_owasp_useful_headers_set(
    client_request,
    mocker,
    mock_get_service_and_organisation_counts,
):
    client_request.logout()
    response = client_request.get_response('.index')

    assert response.headers['X-Frame-Options'] == 'deny'
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert response.headers['X-XSS-Protection'] == '1; mode=block'
    assert response.headers['Content-Security-Policy'] == (
        "default-src 'self' static.example.com; "
        "script-src 'self' static.example.com *.google-analytics.com https://js-agent.newrelic.com "
        "https://*.nr-data.net data:; "
        "connect-src 'self' *.google-analytics.com https://*.nr-data.net; "
        "font-src 'self' static.example.com data:; "
        "img-src "
        "'self' static.example.com static-logos.test.com"
        " *.google-analytics.com data:"
    )
