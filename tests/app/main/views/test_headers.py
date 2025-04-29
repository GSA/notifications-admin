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
    api_host_name = current_app.config.get("API_HOST_NAME")
    assert api_host_name is not None, f"API_HOST_NAME: {api_host_name} — is missing"

    assert api_host_name in csp
    if api_host_name.startswith("http://"):
        assert api_host_name.replace("http://", "ws://") in csp
    elif api_host_name.startswith("https://"):
        assert api_host_name.replace("https://", "wss://") in csp
    else:
        raise AssertionError(
            f"Unexpected API_HOST_NAME format: {api_host_name} — must start with 'http://' or 'https://'"
        )
