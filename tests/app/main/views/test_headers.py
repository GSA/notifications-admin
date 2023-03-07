from re import search


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
    csp = response.headers['Content-Security-Policy']
    assert search(r"default-src 'self' static\.example\.com;", csp)
    assert search(
        r"script-src 'self' 'unsafe-eval' static\.example\.com \*\.google-analytics\.com https:\/\/js-agent\.newrelic\.com https:\/\/\*\.nr-data\.net data: 'nonce-.*';", # noqa e501
        csp
    )
    assert search(r"connect-src 'self' \*\.google-analytics\.com https:\/\/\*.nr-data\.net;", csp)
    assert search(r"style-src 'self' static\.example\.com 'nonce-.*';", csp)
    assert search(r"font-src 'self' static\.example\.com data:;", csp)
    assert search(r"img-src 'self' static\.example\.com static-logos\.test\.com \*\.google-analytics\.com data:", csp)
