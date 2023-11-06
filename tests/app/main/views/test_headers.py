from re import search


def test_owasp_useful_headers_set(
    client_request,
    mocker,
    mock_get_service_and_organization_counts,
):
    client_request.logout()
    response = client_request.get_response(".index")

    assert response.headers["X-Frame-Options"] == "deny"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    csp = response.headers["Content-Security-Policy"]
    assert search(r"default-src 'self' static\.example\.com;", csp)
    assert search(r"frame-ancestors 'none';", csp)
    assert search(r"form-action 'self';", csp)
    assert search(
        r"script-src 'self' static\.example\.com 'unsafe-eval' https:\/\/js-agent\.new"
        r"relic\.com https:\/\/gov-bam\.nr-data\.net 'nonce-.*';",
        csp,
    )
    assert search(r"connect-src 'self' https:\/\/gov-bam.nr-data\.net;", csp)
    assert search(r"style-src 'self' static\.example\.com 'nonce-.*';", csp)
    assert search(r"img-src 'self' static\.example\.com static-logos\.test\.com", csp)
