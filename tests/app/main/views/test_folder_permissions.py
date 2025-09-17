from bs4 import BeautifulSoup
from flask import url_for

from tests.conftest import SERVICE_ONE_ID, USER_ONE_ID


def test_select_all_button_works(client, mocker):
    mocker.patch('app.service_api_client.get_service', return_value={'data': {
        'id': SERVICE_ONE_ID,
    }})

    mocker.patch('app.user_api_client.get_user', return_value={
        'id': USER_ONE_ID,
        'platform_admin': False,
    })

    page = client.get(
        url_for('main.edit_user_permissions', service_id=SERVICE_ONE_ID, user_id=USER_ONE_ID)
    )
    soup = BeautifulSoup(page.data.decode('utf-8'), 'html.parser')

    button = soup.find('button', {'id': 'select-all-folders'})
    assert button is not None
    assert button.text.strip() in ['Select all', 'Deselect all']


def test_javascript_parent_child_logic_exists(client, mocker):
    mocker.patch('app.service_api_client.get_service', return_value={'data': {
        'id': SERVICE_ONE_ID,
    }})

    mocker.patch('app.user_api_client.get_user', return_value={
        'id': USER_ONE_ID,
        'platform_admin': False,
    })

    page = client.get(
        url_for('main.edit_user_permissions', service_id=SERVICE_ONE_ID, user_id=USER_ONE_ID)
    )
    html = page.data.decode('utf-8')

    assert 'handleParentSelection' in html
    assert 'data-parent-id' in html
    assert 'toggleSelectAll' in html


def test_hidden_from_platform_admins(client, mocker):
    mocker.patch('app.service_api_client.get_service', return_value={'data': {
        'id': SERVICE_ONE_ID,
    }})

    mocker.patch('app.user_api_client.get_user', return_value={
        'id': USER_ONE_ID,
        'platform_admin': True,
    })

    page = client.get(
        url_for('main.edit_user_permissions', service_id=SERVICE_ONE_ID, user_id=USER_ONE_ID)
    )
    soup = BeautifulSoup(page.data.decode('utf-8'), 'html.parser')

    assert 'Platform admin users can access all template folders' in page.data.decode('utf-8')

    folder_container = soup.find('div', {'id': 'custom-folder-permissions'})
    assert folder_container is None
