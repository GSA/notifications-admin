import json
import uuid

import pytest
from flask import url_for
from notifications_utils.url_safe_token import generate_token

from tests.conftest import (
    create_api_user_active,
    create_user,
    normalize_spaces,
    url_for_endpoint_with_token,
)


def test_should_show_overview_page(
    client_request,
):
    page = client_request.get('main.user_profile')
    assert page.select_one('h1').text.strip() == 'Your profile'
    assert 'Use platform admin view' not in page
    assert 'Security keys' not in page


def test_overview_page_shows_disable_for_platform_admin(
    client_request,
    platform_admin_user
):
    client_request.login(platform_admin_user)
    page = client_request.get('main.user_profile')
    assert page.select_one('h1').text.strip() == 'Your profile'
    disable_platform_admin_row = page.select_one('#disable-platform-admin')
    assert ' '.join(disable_platform_admin_row.text.split()) == \
        'Use platform admin view Yes Change whether to use platform admin view'


def test_should_show_name_page(
    client_request
):
    page = client_request.get(('main.user_profile_name'))
    assert page.select_one('h1').text.strip() == 'Change your name'


def test_should_redirect_after_name_change(
    client_request,
    mock_update_user_attribute,
):
    client_request.post(
        'main.user_profile_name',
        _data={'new_name': 'New Name'},
        _expected_status=302,
        _expected_redirect=url_for('main.user_profile'),
    )
    assert mock_update_user_attribute.called is True


def test_should_show_email_page(
    client_request,
):
    page = client_request.get(
        'main.user_profile_email'
    )
    assert page.select_one('h1').text.strip() == 'Change your email address'
    # template is shared with "Change your mobile number" but we don't want to show Delete mobile number link
    assert 'Delete your number' not in page.text


def test_should_redirect_after_email_change(
    client_request,
    mock_login,
    mock_email_is_not_already_in_use,
):
    client_request.post(
        'main.user_profile_email',
        _data={'email_address': 'new_notify@notify.gsa.gov'},
        _expected_status=302,
        _expected_redirect=url_for(
            'main.user_profile_email_authenticate',
        )
    )

    assert mock_email_is_not_already_in_use.called


@pytest.mark.parametrize('email_address,error_message', [
    ('me@example.com', 'Enter a public sector email address or find out who can use Notify'),
    ('not_valid', 'Enter a valid email address')  # 2 errors with email address, only first error shown
])
def test_should_show_errors_if_new_email_address_does_not_validate(
    client_request,
    mock_email_is_not_already_in_use,
    mock_get_organizations,
    email_address,
    error_message,
):
    page = client_request.post(
        'main.user_profile_email',
        _data={'email_address': email_address},
        _expected_status=200,
    )

    assert normalize_spaces(page.find('span', class_='usa-error-message').text) == f'Error: {error_message}'
    # We only call API to check if the email address is already in use if there are no other errors
    assert not mock_email_is_not_already_in_use.called


def test_should_show_authenticate_after_email_change(
    client_request,
):
    with client_request.session_transaction() as session:
        session['new-email'] = 'new_notify@notify.gsa.gov'

    page = client_request.get('main.user_profile_email_authenticate')

    assert 'Change your email address' in page.text
    assert 'Confirm' in page.text


def test_should_render_change_email_continue_after_authenticate_email(
    client_request,
    mock_verify_password,
    mock_send_change_email_verification,
):
    with client_request.session_transaction() as session:
        session['new-email'] = 'new_notify@notify.gsa.gov'
    page = client_request.post(
        'main.user_profile_email_authenticate',
        _data={'password': '12345'},
        _expected_status=200,
    )
    assert 'Click the link in the email to confirm the change to your email address.' in page.text


def test_should_redirect_to_user_profile_when_user_confirms_email_link(
    notify_admin,
    client_request,
    api_user_active,
    mock_update_user_attribute,
):

    token = generate_token(payload=json.dumps({'user_id': api_user_active['id'], 'email': 'new_email@gsa.gov'}),
                           secret=notify_admin.config['SECRET_KEY'], salt=notify_admin.config['DANGEROUS_SALT'])
    client_request.get_url(
        url_for_endpoint_with_token(
            'main.user_profile_email_confirm',
            token=token,
        ),
        _expected_redirect=url_for('main.user_profile'),
    )


def test_should_show_mobile_number_page(
    client_request,
):
    page = client_request.get(('main.user_profile_mobile_number'))
    assert 'Change your mobile number' in page.text
    assert 'Delete your number' not in page.text


def test_change_your_mobile_number_page_shows_delete_link_if_user_on_email_auth(
    client_request,
    api_user_active_email_auth,
    mocker
):
    client_request.login(api_user_active_email_auth)
    page = client_request.get(('main.user_profile_mobile_number'))
    assert 'Change your mobile number' in page.text
    assert 'Delete your number' in page.text


def test_change_your_mobile_number_page_doesnt_show_delete_link_if_user_has_no_mobile_number(
    client_request,
    fake_uuid,
    mocker
):
    user = create_user(
        id=fake_uuid,
        auth_type='email_auth',
        mobile_number=None
    )
    client_request.login(user)
    page = client_request.get(('main.user_profile_mobile_number'))
    assert 'Change your mobile number' in page.text
    assert 'Delete your number' not in page.text


def test_confirm_delete_mobile_number(
    client_request,
    api_user_active_email_auth,
    mocker
):
    client_request.login(api_user_active_email_auth)

    page = client_request.get(
        '.user_profile_confirm_delete_mobile_number',
        _test_page_title=False,
    )

    assert normalize_spaces(page.select_one('.banner-dangerous').text) == (
        'Are you sure you want to delete your mobile number from Notify? '
        'Yes, delete'
    )
    assert 'action' not in page.select_one('.banner-dangerous form')
    assert page.select_one('.banner-dangerous form')['method'] == 'post'


def test_delete_mobile_number(
    client_request,
    api_user_active_email_auth,
    mocker
):
    client_request.login(api_user_active_email_auth)
    mock_delete = mocker.patch('app.user_api_client.update_user_attribute')

    client_request.post(
        '.user_profile_mobile_number_delete',
        _expected_redirect=url_for(
            '.user_profile',
        )
    )
    mock_delete.assert_called_once_with(
        api_user_active_email_auth["id"],
        mobile_number=None
    )


@pytest.mark.parametrize('phone_number_to_register_with', [
    '+12024900460',
    '+1800-555-5555',
])
def test_should_redirect_after_mobile_number_change(
    client_request,
    phone_number_to_register_with,
):
    client_request.post(
        'main.user_profile_mobile_number',
        _data={'mobile_number': phone_number_to_register_with},
        _expected_status=302,
        _expected_redirect=url_for(
            'main.user_profile_mobile_number_authenticate',
        )
    )
    with client_request.session_transaction() as session:
        assert session['new-mob'] == phone_number_to_register_with


def test_should_show_authenticate_after_mobile_number_change(
    client_request,
):
    with client_request.session_transaction() as session:
        session['new-mob'] = '+12021234123'

    page = client_request.get(
        'main.user_profile_mobile_number_authenticate',
    )

    assert 'Change your mobile number' in page.text
    assert 'Confirm' in page.text


def test_should_redirect_after_mobile_number_authenticate(
    client_request,
    mock_verify_password,
    mock_send_verify_code,
):
    with client_request.session_transaction() as session:
        session['new-mob'] = '+12021234123'

    client_request.post(
        'main.user_profile_mobile_number_authenticate',
        _data={'password': '12345667'},
        _expected_status=302,
        _expected_redirect=url_for(
            'main.user_profile_mobile_number_confirm',
        )
    )


def test_should_show_confirm_after_mobile_number_change(
    client_request,
):
    with client_request.session_transaction() as session:
        session['new-mob-password-confirmed'] = True
    page = client_request.get(
        'main.user_profile_mobile_number_confirm'
    )

    assert 'Change your mobile number' in page.text
    assert 'Confirm' in page.text


@pytest.mark.parametrize('phone_number_to_register_with', [
    '+12020900460',
    '+1800-555-555',
])
def test_should_redirect_after_mobile_number_confirm(
    client_request,
    mocker,
    mock_update_user_attribute,
    mock_check_verify_code,
    phone_number_to_register_with,
):
    user_before = create_api_user_active(with_unique_id=True)
    user_after = create_api_user_active(with_unique_id=True)
    user_before['current_session_id'] = str(uuid.UUID(int=1))
    user_after['current_session_id'] = str(uuid.UUID(int=2))

    client_request.login(user_before)
    mocker.patch('app.user_api_client.get_user', side_effect=[user_after])

    with client_request.session_transaction() as session:
        session['new-mob-password-confirmed'] = True
        session['new-mob'] = phone_number_to_register_with
        session['current_session_id'] = user_before['current_session_id']

    client_request.post(
        'main.user_profile_mobile_number_confirm',
        _data={'sms_code': '123456'},
        _expected_status=302,
        _expected_redirect=url_for(
            'main.user_profile',
        )
    )

    # make sure the current_session_id has changed to what the API returned
    with client_request.session_transaction() as session:
        assert session['current_session_id'] == user_after['current_session_id']


def test_should_show_password_page(
    client_request,
):
    page = client_request.get(('main.user_profile_password'))

    assert page.select_one('h1').text.strip() == 'Change your password'


def test_should_redirect_after_password_change(
    client_request,
    mock_update_user_password,
    mock_verify_password,
):
    client_request.post(
        'main.user_profile_password',
        _data={
            'new_password': 'the new password',
            'old_password': 'the old password',
        },
        _expected_status=302,
        _expected_redirect=url_for(
            'main.user_profile',
        ),
    )


def test_non_gov_user_cannot_see_change_email_link(
    client_request,
    api_nongov_user_active,
    mock_get_organizations,
):
    client_request.login(api_nongov_user_active)
    page = client_request.get('main.user_profile')
    assert not page.find('a', {'href': url_for('main.user_profile_email')})
    assert page.select_one('h1').text.strip() == 'Your profile'


def test_non_gov_user_cannot_access_change_email_page(
    client_request,
    api_nongov_user_active,
    mock_get_organizations,
):
    client_request.login(api_nongov_user_active)
    client_request.get('main.user_profile_email', _expected_status=403)


def test_normal_user_doesnt_see_disable_platform_admin(client_request):
    client_request.get('main.user_profile_disable_platform_admin_view', _expected_status=403)


def test_platform_admin_can_see_disable_platform_admin_page(client_request, platform_admin_user):
    client_request.login(platform_admin_user)
    page = client_request.get('main.user_profile_disable_platform_admin_view')

    assert page.select_one('h1').text.strip() == 'Use platform admin view'
    assert page.select_one('input[checked]')['value'] == 'True'


def test_can_disable_platform_admin(client_request, platform_admin_user):
    client_request.login(platform_admin_user)

    with client_request.session_transaction() as session:
        assert 'disable_platform_admin_view' not in session

    client_request.post(
        'main.user_profile_disable_platform_admin_view',
        _data={'enabled': False},
        _expected_status=302,
        _expected_redirect=url_for('main.user_profile'),
    )

    with client_request.session_transaction() as session:
        assert session['disable_platform_admin_view'] is True


def test_can_reenable_platform_admin(client_request, platform_admin_user):
    client_request.login(platform_admin_user)

    with client_request.session_transaction() as session:
        session['disable_platform_admin_view'] = True

    client_request.post(
        'main.user_profile_disable_platform_admin_view',
        _data={'enabled': True},
        _expected_status=302,
        _expected_redirect=url_for('main.user_profile'),
    )

    with client_request.session_transaction() as session:
        assert session['disable_platform_admin_view'] is False
