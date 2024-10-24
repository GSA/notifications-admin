import pytest


@pytest.mark.parametrize(
    "url",
    [
        "/security.txt",
        "/.well-known/security.txt",
    ],
)
def test_security_policy_redirects_to_policy(client_request, url):
    client_request.get_url(
        url,
        _test_page_title=False,
        _expected_status=200,
    )
