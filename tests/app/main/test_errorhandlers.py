import pytest
from flask import Response, url_for
from flask_wtf.csrf import CSRFError
from notifications_python_client.errors import HTTPError


def test_bad_url_returns_page_not_found(client_request):
    page = client_request.get_url(
        '/bad_url',
        _expected_status=404,
    )
    assert page.h1.string.strip() == 'Page not found'
    assert page.title.string.strip() == 'Page not found – U.S. Notify'


def test_load_service_before_request_handles_404(client_request, mocker):
    exc = HTTPError(Response(status=404), 'Not found')
    get_service = mocker.patch('app.service_api_client.get_service', side_effect=exc)

    client_request.get(
        'main.service_dashboard',
        service_id='00000000-0000-0000-0000-000000000000',
        _expected_status=404
    )

    get_service.assert_called_once_with('00000000-0000-0000-0000-000000000000')


@pytest.mark.parametrize('url', [
    '/new-password/MALFORMED_TOKEN',
    '/user-profile/email/confirm/MALFORMED_TOKEN',
    '/verify-email/MALFORMED_TOKEN'
])
def test_malformed_token_returns_page_not_found(client_request, url):
    page = client_request.get_url(url, _expected_status=404)

    assert page.h1.string.strip() == 'Page not found'
    flash_banner = page.find('div', class_='banner-dangerous').string.strip()
    assert flash_banner == "There’s something wrong with the link you’ve used."
    assert page.title.string.strip() == 'Page not found – U.S. Notify'


def test_csrf_returns_400(client_request, mocker):
    # we turn off CSRF handling for tests, so fake a CSRF response here.
    csrf_err = CSRFError('400 Bad Request: The CSRF tokens do not match.')
    mocker.patch('app.main.views.index.render_template', side_effect=csrf_err)

    page = client_request.get_url(
        '/cookies',
        _expected_status=400,
        _test_page_title=False,
    )

    assert page.h1.string.strip() == 'Sorry, there’s a problem with U.S. Notify'
    assert page.title.string.strip() == 'Sorry, there’s a problem with the service – U.S. Notify'


def test_csrf_redirects_to_sign_in_page_if_not_signed_in(client_request, mocker):
    csrf_err = CSRFError('400 Bad Request: The CSRF tokens do not match.')
    mocker.patch('app.main.views.index.render_template', side_effect=csrf_err)

    client_request.logout()
    client_request.get_url(
        '/cookies',
        _expected_redirect=url_for('main.sign_in', next='/cookies'),
    )


def test_405_returns_something_went_wrong_page(client_request, mocker):
    page = client_request.post_url('/', _expected_status=405)

    assert page.h1.string.strip() == 'Sorry, there’s a problem with U.S. Notify'
    assert page.title.string.strip() == 'Sorry, there’s a problem with the service – U.S. Notify'
