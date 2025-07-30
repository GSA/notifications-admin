from re import search


def test_owasp_useful_headers_set(
    client_request,
    mocker,
    mock_get_service_and_organization_counts,
):

    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()
    response = client_request.get_response(".index")

    assert response.headers["X-Frame-Options"] == "deny"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    csp = response.headers["Content-Security-Policy"]
    assert search(r"frame-src.*https://www\.googletagmanager\.com", csp)
    assert search(r"frame-ancestors 'none';", csp)
    assert search(r"form-action 'self';", csp)
    assert search(
        r"script-src 'self' static\.example\.com 'unsafe-eval' https:\/\/js-agent\.new"
        r"relic\.com https:\/\/gov-bam\.nr-data\.net https:\/\/www\.googletagmanager\."
        r"com https:\/\/www\.google-analytics\.com https:\/\/dap\.digitalgov\.gov "
        r"https:\/\/cdn\.socket\.io",
        csp,
    )
    assert search(r"'nonce-[^']+';", csp)
    connect_src = next(
        (
            directive
            for directive in csp.split(";")
            if directive.strip().startswith("connect-src")
        ),
        None,
    )
    assert connect_src is not None, "connect-src directive is missing"
    from flask import current_app

    config = current_app.config
    expected_sources = {
        "'self'",
        "https://gov-bam.nr-data.net",
        "https://www.google-analytics.com",
        config["API_PUBLIC_URL"],
        config["API_PUBLIC_WS_URL"],
    }
    actual_sources = set(connect_src.strip().split()[1:])
    assert (
        expected_sources <= actual_sources
    ), f"Missing sources in connect-src: {expected_sources - actual_sources}"
    assert search(r"style-src 'self' static\.example\.com 'nonce-.*';", csp)
    assert search(r"img-src 'self' static\.example\.com", csp)
