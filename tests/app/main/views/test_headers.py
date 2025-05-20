from re import search

from flask import current_app


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
    assert search(
        r"connect-src 'self' https:\/\/gov-bam\.nr-data\.net https:\/\/www\.google-analytics\.",
        csp,
    )
    assert search(r"style-src 'self' static\.example\.com 'nonce-.*';", csp)
    assert search(r"img-src 'self' static\.example\.com static-logos\.test\.com", csp)
    api_public_url = current_app.config.get("API_PUBLIC_URL")
    assert api_public_url is not None, f"API_PUBLIC_URL: {api_public_url} — is missing"

    assert api_public_url in csp
    if api_public_url.startswith("http://"):
        assert api_public_url.replace("http://", "ws://") in csp
    elif api_public_url.startswith("https://"):
        assert api_public_url.replace("https://", "wss://") in csp
    else:
        raise AssertionError(
            f"Unexpected API_PUBLIC_URL format: {api_public_url} — must start with 'http://' or 'https://'"
        )
