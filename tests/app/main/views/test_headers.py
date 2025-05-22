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
    assert search(r"connect-src", csp)
    assert search(r"https:\/\/gov-bam\.nr-data\.net", csp)
    assert search(r"https:\/\/www\.google-analytics\.com", csp)
    assert search(r"http:\/\/localhost:6011", csp)
    assert search(r"ws:\/\/localhost:6011", csp)
    assert search(r"https:\/\/notify-api-.*\.app\.cloud\.gov", csp)
    assert search(r"wss:\/\/notify-api-.*\.app\.cloud\.gov", csp)
    assert search(r"style-src 'self' static\.example\.com 'nonce-.*';", csp)
    assert search(r"img-src 'self' static\.example\.com static-logos\.test\.com", csp)
