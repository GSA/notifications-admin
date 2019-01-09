import re
from datetime import datetime
from unittest.mock import ANY, Mock

import pytest
from bs4 import BeautifulSoup
from flask import url_for
from freezegun import freeze_time
from notifications_python_client.errors import HTTPError

from app.main.views.templates import (
    get_human_readable_delta,
    get_last_use_message,
)
from tests import (
    single_notification_json,
    template_json,
    validate_route_permission,
)
from tests.app.main.views.test_template_folders import (
    CHILD_FOLDER_ID,
    FOLDER_TWO_ID,
    PARENT_FOLDER_ID,
    _folder,
    _template,
)
from tests.conftest import (
    SERVICE_ONE_ID,
    SERVICE_TWO_ID,
    TEMPLATE_ONE_ID,
    ElementNotFound,
    active_caseworking_user,
    active_user_view_permissions,
    mock_get_service_email_template,
    mock_get_service_letter_template,
    mock_get_service_template,
    no_letter_contact_blocks,
    normalize_spaces,
)
from tests.conftest import service_one as create_sample_service
from tests.conftest import single_letter_contact_block


def test_should_show_empty_page_when_no_templates(
    client_request,
    service_one,
    mock_get_organisations_and_services_for_user,
    mock_get_service_templates_when_no_templates_exist,
    mock_get_template_folders,
):

    page = client_request.get(
        'main.choose_template',
        service_id=service_one['id'],
    )

    assert normalize_spaces(page.select_one('h1').text) == (
        'Templates'
    )
    assert normalize_spaces(page.select_one('main p').text) == (
        'You need a template before you can send emails or text messages.'
    )
    assert page.select_one('main a')['href'] == url_for(
        'main.add_template_by_type',
        service_id=service_one['id'],
    )
    assert len(page.select('main a')) == 1


def test_should_show_add_template_form_if_service_has_folder_permission(
    client_request,
    service_one,
    mock_get_organisations_and_services_for_user,
    mock_get_service_templates_when_no_templates_exist,
    mock_get_template_folders,
):

    service_one['permissions'] += ['edit_folders']

    page = client_request.get(
        'main.choose_template',
        service_id=service_one['id'],
    )

    assert normalize_spaces(page.select_one('h1').text) == (
        'Templates'
    )
    assert normalize_spaces(page.select_one('main p').text) == (
        'You need a template before you can send emails or text messages.'
    )
    assert [
        (item['name'], item['value']) for item in page.select('[type=radio]')
    ] == [
        ('add_template_by_template_type', 'email'),
        ('add_template_by_template_type', 'sms'),
    ]
    assert not page.select('main a')


@pytest.mark.parametrize(
    'user, expected_page_title, extra_args, expected_nav_links, expected_templates',
    [
        (
            active_user_view_permissions,
            'Templates',
            {},
            ['Text message', 'Email', 'Letter'],
            [
                'sms_template_one',
                'sms_template_two',
                'email_template_one',
                'email_template_two',
                'letter_template_one',
                'letter_template_two',
            ]
        ),
        (
            active_user_view_permissions,
            'Templates',
            {'template_type': 'sms'},
            ['All', 'Email', 'Letter'],
            ['sms_template_one', 'sms_template_two'],
        ),
        (
            active_user_view_permissions,
            'Templates',
            {'template_type': 'email'},
            ['All', 'Text message', 'Letter'],
            ['email_template_one', 'email_template_two'],
        ),
        (
            active_user_view_permissions,
            'Templates',
            {'template_type': 'letter'},
            ['All', 'Text message', 'Email'],
            ['letter_template_one', 'letter_template_two'],
        ),
        (
            active_caseworking_user,
            'Templates',
            {},
            ['Text message', 'Email', 'Letter'],
            [
                'sms_template_one',
                'sms_template_two',
                'email_template_one',
                'email_template_two',
                'letter_template_one',
                'letter_template_two',
            ],
        ),
        (
            active_caseworking_user,
            'Templates',
            {'template_type': 'email'},
            ['All', 'Text message', 'Letter'],
            ['email_template_one', 'email_template_two'],
        ),
    ]
)
def test_should_show_page_for_choosing_a_template(
    client_request,
    mock_get_organisations_and_services_for_user,
    mock_get_service_templates,
    mock_get_template_folders,
    mock_has_no_jobs,
    extra_args,
    expected_nav_links,
    expected_templates,
    service_one,
    mocker,
    fake_uuid,
    user,
    expected_page_title,
):
    service_one['permissions'].append('letter')
    client_request.login(user(fake_uuid))

    page = client_request.get(
        'main.choose_template',
        service_id=service_one['id'],
        **extra_args
    )

    assert normalize_spaces(page.select_one('h1').text) == expected_page_title

    links_in_page = page.select('.pill a')

    assert len(links_in_page) == len(expected_nav_links)

    for index, expected_link in enumerate(expected_nav_links):
        assert links_in_page[index].text.strip() == expected_link

    template_links = page.select('.message-name a')

    assert len(template_links) == len(expected_templates)

    for index, expected_template in enumerate(expected_templates):
        assert template_links[index].text.strip() == expected_template

    mock_get_service_templates.assert_called_once_with(SERVICE_ONE_ID)
    mock_get_template_folders.assert_called_once_with(SERVICE_ONE_ID)


def test_should_not_show_template_nav_if_only_one_type_of_template(
    client_request,
    mock_get_template_folders,
    mock_get_service_templates_with_only_one_template,
):

    page = client_request.get(
        'main.choose_template',
        service_id=SERVICE_ONE_ID,
    )

    assert not page.select('.pill')


def test_should_not_show_live_search_if_list_of_templates_fits_onscreen(
    client_request,
    mock_get_template_folders,
    mock_get_service_templates
):

    page = client_request.get(
        'main.choose_template',
        service_id=SERVICE_ONE_ID,
    )

    assert not page.select('.live-search')


def test_should_show_live_search_if_list_of_templates_taller_than_screen(
    client_request,
    mock_get_template_folders,
    mock_get_more_service_templates_than_can_fit_onscreen
):

    page = client_request.get(
        'main.choose_template',
        service_id=SERVICE_ONE_ID,
    )
    search = page.select_one('.live-search')

    assert search['data-module'] == 'live-search'
    assert search['data-targets'] == '#template-list .template-list-item'

    assert len(page.select(search['data-targets'])) == len(page.select('.message-name')) == 14


def test_should_show_live_search_if_service_has_lots_of_folders(
    client_request,
    mock_get_template_folders,
    mock_get_service_templates,  # returns 4 templates
):

    mock_get_template_folders.return_value = [
        _folder('one', PARENT_FOLDER_ID),
        _folder('two', None, parent=PARENT_FOLDER_ID),
        _folder('three', None, parent=PARENT_FOLDER_ID),
        _folder('four', None, parent=PARENT_FOLDER_ID),
    ]

    page = client_request.get(
        'main.choose_template',
        service_id=SERVICE_ONE_ID,
    )

    count_of_templates_and_folders = len(page.select('.message-name'))
    count_of_folders = len(page.select('.template-list-folder'))
    count_of_templates = count_of_templates_and_folders - count_of_folders

    assert len(page.select('.live-search')) == 1
    assert count_of_folders == 4
    assert count_of_templates == 4


@pytest.mark.parametrize('extra_permissions, expected_values, expected_labels', (
    pytest.param(['edit_folders'], [
        'email',
        'sms',
        'copy-existing',
    ], [
        'Email template',
        'Text message template',
        'Copy of an existing template',
    ]),
    pytest.param(['edit_folders', 'letter'], [
        'email',
        'sms',
        'letter',
        'copy-existing',
    ], [
        'Email template',
        'Text message template',
        'Letter template',
        'Copy of an existing template',
    ]),
    pytest.param(
        [], [], [],
        marks=pytest.mark.xfail(raises=ElementNotFound)
    ),
))
def test_should_show_new_template_choices_if_service_has_folder_permission(
    client_request,
    service_one,
    mock_get_organisations_and_services_for_user,
    mock_get_service_templates,
    mock_get_template_folders,
    extra_permissions,
    expected_values,
    expected_labels,
):
    service_one['permissions'] += extra_permissions

    page = client_request.get(
        'main.choose_template',
        service_id=SERVICE_ONE_ID,
    )

    if not page.select('#add_new_template_form'):
        raise ElementNotFound()

    assert normalize_spaces(page.select_one('#add_new_template_form fieldset fieldset legend').text) == (
        'Add new'
    )
    assert [
        choice['value'] for choice in page.select('#add_new_template_form input[type=radio]')
    ] == expected_values
    assert [
        normalize_spaces(choice.text) for choice in page.select('#add_new_template_form label')
    ] == expected_labels


def test_should_show_page_for_one_template(
    logged_in_client,
    mock_get_service_template,
    service_one,
    fake_uuid,
):
    template_id = fake_uuid
    response = logged_in_client.get(url_for(
        '.edit_service_template',
        service_id=service_one['id'],
        template_id=template_id))

    assert response.status_code == 200
    assert "Two week reminder" in response.get_data(as_text=True)
    assert "Template &lt;em&gt;content&lt;/em&gt; with &amp; entity" in response.get_data(as_text=True)
    assert "Use priority queue?" not in response.get_data(as_text=True)
    mock_get_service_template.assert_called_with(service_one['id'], template_id)


def test_caseworker_redirected_to_one_off(
    client_request,
    mock_get_service_templates,
    mock_get_service_template,
    mocker,
    fake_uuid,
):

    mocker.patch('app.user_api_client.get_user', return_value=active_caseworking_user(fake_uuid))

    client_request.get(
        'main.view_template',
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _expected_status=302,
        _expected_redirect=url_for(
            'main.send_one_off',
            service_id=SERVICE_ONE_ID,
            template_id=fake_uuid,
            _external=True,
        ),
    )


def test_user_with_only_send_and_view_redirected_to_one_off(
    client_request,
    mock_get_service_templates,
    mock_get_service_template,
    active_user_with_permissions,
    mocker,
    fake_uuid,
):
    active_user_with_permissions._permissions[SERVICE_ONE_ID] = [
        'send_messages',
        'view_activity',
    ]
    client_request.login(active_user_with_permissions)
    client_request.get(
        'main.view_template',
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _expected_status=302,
        _expected_redirect=url_for(
            'main.send_one_off',
            service_id=SERVICE_ONE_ID,
            template_id=fake_uuid,
            _external=True,
        ),
    )


@pytest.mark.parametrize('permissions', (
    {'send_messages', 'view_activity'},
    {'send_messages'},
    {'view_activity'},
    {},
))
def test_user_with_only_send_and_view_sees_letter_page(
    client_request,
    mock_get_service_templates,
    mock_get_template_folders,
    mock_get_service_letter_template,
    single_letter_contact_block,
    mock_has_jobs,
    active_user_with_permissions,
    mocker,
    fake_uuid,
    permissions,
):
    mocker.patch('app.main.views.templates.get_page_count_for_letter', return_value=1)
    active_user_with_permissions._permissions[SERVICE_ONE_ID] = permissions
    client_request.login(active_user_with_permissions)
    page = client_request.get(
        'main.view_template',
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
    )
    assert page.select_one('h1').text.strip() == 'Two week reminder'


@pytest.mark.parametrize("permissions,template_postage,expected_result", [
    (["choose_postage", "letter"], "first", "Postage: first class"),
    (["choose_postage", "letter"], "second", "Postage: second class"),
    (["choose_postage", "letter"], None, "Postage: second class"),
    pytest.param(
        ["letter"], None, "Postage: second class",
        marks=pytest.mark.xfail(raises=AttributeError)
    ),
])
def test_view_letter_template_displays_postage_dynamically_based_on_service_permissions_and_template_postage(
    client_request,
    service_one,
    mock_get_service_templates,
    mock_get_template_folders,
    single_letter_contact_block,
    mock_has_jobs,
    active_user_with_permissions,
    mocker,
    fake_uuid,
    permissions,
    template_postage,
    expected_result
):
    mocker.patch('app.main.views.templates.get_page_count_for_letter', return_value=1)
    service_one['permissions'] = permissions
    client_request.login(active_user_with_permissions)
    mock_get_service_letter_template(mocker, postage=template_postage)
    page = client_request.get(
        'main.view_template',
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
    )

    assert normalize_spaces(page.select_one('#postage').text) == expected_result


def test_view_non_letter_template_does_not_display_postage(
    logged_in_client,
    mock_get_service_template,
    mock_get_template_folders,
    service_one,
    fake_uuid,
):

    response = logged_in_client.get(url_for(
        '.view_template',
        service_id=service_one['id'],
        template_id=fake_uuid))

    assert response.status_code == 200

    page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
    assert "Postage" not in page.text


@pytest.mark.parametrize("permissions, expected_result", [
    (["choose_postage", "letter"], True),
    (["letter"], False),
])
def test_edit_letter_templates_postage_choice_visibility_and_default(
    client_request,
    service_one,
    active_user_with_permissions,
    mocker,
    fake_uuid,
    permissions,
    expected_result
):
    mocker.patch('app.main.views.templates.get_page_count_for_letter', return_value=1)
    service_one['permissions'] = permissions
    client_request.login(active_user_with_permissions)
    mock_get_service_letter_template(mocker)
    page = client_request.get(
        'main.edit_service_template',
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
    )
    assert bool(page.find(string=re.compile("Choose postage"))) is expected_result

    if expected_result:
        assert page.select('input[checked]')[0].attrs["value"] == 'None'


@pytest.mark.parametrize("permissions, expected_result", [
    (["choose_postage", "letter"], "first"),
    (["letter"], None),
])
def test_edit_letter_templates_postage_permissions(
    logged_in_client,
    service_one,
    mocker,
    fake_uuid,
    mock_update_service_template,
    permissions,
    expected_result
):
    service_one['permissions'] = permissions
    mock_get_service_letter_template(mocker)
    template_id = fake_uuid

    logged_in_client.post(
        url_for(
            'main.edit_service_template',
            service_id=SERVICE_ONE_ID,
            template_id=template_id
        ),
        data={
            'name': 'Two week reminder',
            'template_content': "Some content",
            'subject': 'Subject',
            'postage': 'first'
        }
    )
    mock_update_service_template.assert_called_with(
        template_id,
        'Two week reminder',
        'letter',
        "Some content",
        SERVICE_ONE_ID,
        'Subject',
        'normal',
        postage=expected_result
    )


@pytest.mark.parametrize('permissions, links_to_be_shown, permissions_warning_to_be_shown', [
    (
        ['view_activity'],
        [],
        'If you need to send this text message or edit this template, contact your manager.'
    ),
    (
        ['manage_api_keys'],
        [],
        None,
    ),
    (
        ['manage_templates'],
        ['.edit_service_template'],
        None,
    ),
    (
        ['send_messages', 'manage_templates'],
        ['.set_sender', '.edit_service_template'],
        None,
    ),
])
def test_should_be_able_to_view_a_template_with_links(
    client,
    mock_get_service_template,
    mock_get_template_folders,
    active_user_with_permissions,
    single_letter_contact_block,
    mocker,
    service_one,
    fake_uuid,
    permissions,
    links_to_be_shown,
    permissions_warning_to_be_shown,
):
    active_user_with_permissions._permissions[service_one['id']] = permissions + ['view_activity']
    client.login(active_user_with_permissions, mocker, service_one)

    response = client.get(url_for(
        '.view_template',
        service_id=service_one['id'],
        template_id=fake_uuid
    ))

    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
    links_in_page = page.select('.pill-separate-item')

    assert len(links_in_page) == len(links_to_be_shown)

    for index, link_to_be_shown in enumerate(links_to_be_shown):
        assert links_in_page[index]['href'] == url_for(
            link_to_be_shown,
            service_id=service_one['id'],
            template_id=fake_uuid,
        )

    assert normalize_spaces(page.select_one('main p').text) == (
        permissions_warning_to_be_shown or 'To: phone number'
    )


def test_should_show_template_id_on_template_page(
    logged_in_client,
    mock_get_service_template,
    mock_get_template_folders,
    service_one,
    fake_uuid,
):

    response = logged_in_client.get(url_for(
        '.view_template',
        service_id=service_one['id'],
        template_id=fake_uuid))

    assert response.status_code == 200

    page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
    assert page.select('.api-key-key')[0].text == fake_uuid


def test_should_show_sms_template_with_downgraded_unicode_characters(
    logged_in_client,
    mocker,
    service_one,
    single_letter_contact_block,
    mock_get_template_folders,
    fake_uuid,
):
    msg = 'here:\tare some “fancy quotes” and zero\u200Bwidth\u200Bspaces'
    rendered_msg = 'here: are some "fancy quotes" and zerowidthspaces'

    mocker.patch(
        'app.service_api_client.get_service_template',
        return_value={'data': template_json(service_one['id'], fake_uuid, type_='sms', content=msg)}
    )

    template_id = fake_uuid
    response = logged_in_client.get(url_for(
        '.view_template',
        service_id=service_one['id'],
        template_id=template_id))

    assert response.status_code == 200
    assert rendered_msg in response.get_data(as_text=True)


def test_should_let_letter_contact_block_be_changed_for_the_template(
    mocker,
    mock_get_service_letter_template,
    mock_get_template_folders,
    no_letter_contact_blocks,
    client_request,
    service_one,
    fake_uuid,
):
    service_one['permissions'].append('letter')
    mocker.patch('app.main.views.templates.get_page_count_for_letter', return_value=1)

    page = client_request.get(
        'main.view_template',
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid
    )

    assert page.find('a', {'class': 'edit-template-link-letter-contact'})['href'] == url_for(
        'main.set_template_sender',
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
    )


def test_should_show_page_template_with_priority_select_if_platform_admin(
    logged_in_platform_admin_client,
    platform_admin_user,
    mocker,
    mock_get_service_template,
    fake_uuid,
):
    mocker.patch('app.user_api_client.get_users_for_service', return_value=[platform_admin_user])
    template_id = fake_uuid
    response = logged_in_platform_admin_client.get(url_for(
        '.edit_service_template',
        service_id='1234',
        template_id=template_id,
    ))

    assert response.status_code == 200
    assert "Two week reminder" in response.get_data(as_text=True)
    assert "Template &lt;em&gt;content&lt;/em&gt; with &amp; entity" in response.get_data(as_text=True)
    assert "Use priority queue?" in response.get_data(as_text=True)
    mock_get_service_template.assert_called_with('1234', template_id)


@pytest.mark.parametrize('filetype', ['pdf', 'png'])
@pytest.mark.parametrize('view, extra_view_args', [
    ('.view_letter_template_preview', {}),
    ('.view_template_version_preview', {'version': 1}),
])
def test_should_show_preview_letter_templates(
    view,
    extra_view_args,
    filetype,
    logged_in_client,
    mock_get_service_email_template,
    service_one,
    fake_uuid,
    mocker
):
    mocked_preview = mocker.patch(
        'app.main.views.templates.TemplatePreview.from_database_object',
        return_value='foo'
    )

    service_id, template_id = service_one['id'], fake_uuid

    response = logged_in_client.get(url_for(
        view,
        service_id=service_id,
        template_id=template_id,
        filetype=filetype,
        **extra_view_args
    ))

    assert response.status_code == 200
    assert response.get_data(as_text=True) == 'foo'
    mock_get_service_email_template.assert_called_with(service_id, template_id, **extra_view_args)
    assert mocked_preview.call_args[0][0]['id'] == template_id
    assert mocked_preview.call_args[0][0]['service'] == service_id
    assert mocked_preview.call_args[0][1] == filetype


def test_dont_show_preview_letter_templates_for_bad_filetype(
    logged_in_client,
    mock_get_service_template,
    service_one,
    fake_uuid
):
    resp = logged_in_client.get(
        url_for(
            '.view_letter_template_preview',
            service_id=service_one['id'],
            template_id=fake_uuid,
            filetype='blah'
        )
    )
    assert resp.status_code == 404
    assert mock_get_service_template.called is False


@pytest.mark.parametrize('endpoint, data', (
    ('main.add_template_by_type', {
        'template_type': 'copy-existing'
    }),
    ('main.choose_template', {
        'operation': 'add-new-template',
        'add_template_by_template_type': 'copy-existing'
    }),
))
def test_choosing_to_copy_redirects(
    client_request,
    service_one,
    mock_get_service_templates,
    mock_get_template_folders,
    mock_get_organisations_and_services_for_user,
    endpoint,
    data,
):
    service_one['permissions'] += ['edit_folders']
    client_request.post(
        endpoint,
        service_id=SERVICE_ONE_ID,
        _data=data,
        _expected_status=302,
        _expected_redirect=url_for(
            'main.choose_template_to_copy',
            service_id=SERVICE_ONE_ID,
            _external=True,
        ),
    )


def test_choose_a_template_to_copy(
    client_request,
    mock_get_service_templates,
    mock_get_template_folders,
    mock_get_non_empty_organisations_and_services_for_user,
):
    page = client_request.get(
        'main.choose_template_to_copy',
        service_id=SERVICE_ONE_ID,
    )

    assert page.select('.folder-heading') == []

    expected = [
        (
            'Org 1 service 1 '
            '6 templates'
        ),
        (
            'Org 1 service 1 / sms_template_one '
            'Text message template'
        ),
        (
            'Org 1 service 1 / sms_template_two '
            'Text message template'
        ),
        (
            'Org 1 service 1 / email_template_one '
            'Email template'
        ),
        (
            'Org 1 service 1 / email_template_two '
            'Email template'
        ),
        (
            'Org 1 service 1 / letter_template_one '
            'Letter template'
        ),
        (
            'Org 1 service 1 / letter_template_two '
            'Letter template'
        ),
        (
            'Org 1 service 2 '
            '6 templates'
        ),
        (
            'Org 1 service 2 / sms_template_one '
            'Text message template'
        ),
        (
            'Org 1 service 2 / sms_template_two '
            'Text message template'
        ),
        (
            'Org 1 service 2 / email_template_one '
            'Email template'
        ),
        (
            'Org 1 service 2 / email_template_two '
            'Email template'
        ),
        (
            'Org 1 service 2 / letter_template_one '
            'Letter template'
        ),
        (
            'Org 1 service 2 / letter_template_two '
            'Letter template'
        ),
        (
            'Service 1 '
            '6 templates'
        ),
        (
            'Service 1 / sms_template_one '
            'Text message template'
        ),
        (
            'Service 1 / sms_template_two '
            'Text message template'
        ),
        (
            'Service 1 / email_template_one '
            'Email template'
        ),
        (
            'Service 1 / email_template_two '
            'Email template'
        ),
        (
            'Service 1 / letter_template_one '
            'Letter template'
        ),
        (
            'Service 1 / letter_template_two '
            'Letter template'
        ),
        (
            'Service 2 '
            '6 templates'
        ),
        (
            'Service 2 / sms_template_one '
            'Text message template'
        ),
        (
            'Service 2 / sms_template_two '
            'Text message template'
        ),
        (
            'Service 2 / email_template_one '
            'Email template'
        ),
        (
            'Service 2 / email_template_two '
            'Email template'
        ),
        (
            'Service 2 / letter_template_one '
            'Letter template'
        ),
        (
            'Service 2 / letter_template_two '
            'Letter template'
        ),
    ]
    actual = page.select('.template-list-item')

    assert len(actual) == len(expected)

    for actual, expected in zip(actual, expected):
        assert normalize_spaces(actual.text) == expected

    links = page.select('main nav a')
    assert links[0]['href'] == url_for(
        'main.choose_template_to_copy',
        service_id=SERVICE_ONE_ID,
        from_service=SERVICE_TWO_ID,
    )
    assert links[1]['href'] == url_for(
        'main.choose_template_to_copy',
        service_id=SERVICE_ONE_ID,
        from_service=SERVICE_TWO_ID,
    )
    assert links[2]['href'] == url_for(
        'main.copy_template',
        service_id=SERVICE_ONE_ID,
        template_id=TEMPLATE_ONE_ID,
        from_service=SERVICE_TWO_ID,
    )


def test_choose_a_template_to_copy_when_user_has_one_service(
    client_request,
    mock_get_service_templates,
    mock_get_template_folders,
    mock_get_empty_organisations_and_one_service_for_user,
):
    page = client_request.get(
        'main.choose_template_to_copy',
        service_id=SERVICE_ONE_ID,
    )

    assert page.select('.folder-heading') == []

    expected = [
        (
            'sms_template_one '
            'Text message template'
        ),
        (
            'sms_template_two '
            'Text message template'
        ),
        (
            'email_template_one '
            'Email template'
        ),
        (
            'email_template_two '
            'Email template'
        ),
        (
            'letter_template_one '
            'Letter template'
        ),
        (
            'letter_template_two '
            'Letter template'
        ),
    ]
    actual = page.select('.template-list-item')

    assert len(actual) == len(expected)

    for actual, expected in zip(actual, expected):
        assert normalize_spaces(actual.text) == expected

    assert page.select('main nav a')[0]['href'] == url_for(
        'main.copy_template',
        service_id=SERVICE_ONE_ID,
        template_id=TEMPLATE_ONE_ID,
        from_service=SERVICE_TWO_ID,
    )


def test_choose_a_template_to_copy_from_folder_within_service(
    mocker,
    client_request,
    mock_get_template_folders,
    mock_get_non_empty_organisations_and_services_for_user,
):
    mock_get_template_folders.return_value = [
        _folder('Parent folder', PARENT_FOLDER_ID),
        _folder('Child folder empty', CHILD_FOLDER_ID, parent=PARENT_FOLDER_ID),
        _folder('Child folder non-empty', FOLDER_TWO_ID, parent=PARENT_FOLDER_ID),
    ]
    mocker.patch(
        'app.service_api_client.get_service_templates',
        return_value={'data': [
            _template(
                'sms',
                'Should not appear in list (at service root)',
            ),
            _template(
                'sms',
                'Should appear in list (at same level)',
                parent=PARENT_FOLDER_ID,
            ),
            _template(
                'sms',
                'Should appear in list (nested)',
                parent=FOLDER_TWO_ID,
                template_id=TEMPLATE_ONE_ID,
            ),
        ]}
    )
    page = client_request.get(
        'main.choose_template_to_copy',
        service_id=SERVICE_ONE_ID,
        from_service=SERVICE_ONE_ID,
        from_folder=PARENT_FOLDER_ID,
    )

    assert normalize_spaces(page.select_one('.folder-heading').text) == (
        'service one / Parent folder'
    )
    breadcrumb_links = page.select('.folder-heading a')
    assert len(breadcrumb_links) == 1
    assert breadcrumb_links[0]['href'] == url_for(
        'main.choose_template_to_copy',
        service_id=SERVICE_ONE_ID,
        from_service=SERVICE_ONE_ID,
    )

    expected = [
        (
            'Child folder empty '
            'Empty'
        ),
        (
            'Child folder non-empty '
            '1 template'
        ),
        (
            'Child folder non-empty / Should appear in list (nested) '
            'Text message template'
        ),
        (
            'Should appear in list (at same level) '
            'Text message template'
        ),
    ]
    actual = page.select('.template-list-item')

    assert len(actual) == len(expected)

    for actual, expected in zip(actual, expected):
        assert normalize_spaces(actual.text) == expected

    links = page.select('main nav a')
    assert links[0]['href'] == url_for(
        'main.choose_template_to_copy',
        service_id=SERVICE_ONE_ID,
        from_service=SERVICE_ONE_ID,
        from_folder=CHILD_FOLDER_ID,
    )
    assert links[1]['href'] == url_for(
        'main.choose_template_to_copy',
        service_id=SERVICE_ONE_ID,
        from_service=SERVICE_ONE_ID,
        from_folder=FOLDER_TWO_ID,
    )
    assert links[2]['href'] == url_for(
        'main.choose_template_to_copy',
        service_id=SERVICE_ONE_ID,
        from_folder=FOLDER_TWO_ID,
    )
    assert links[3]['href'] == url_for(
        'main.copy_template',
        service_id=SERVICE_ONE_ID,
        template_id=TEMPLATE_ONE_ID,
        from_service=SERVICE_ONE_ID,
    )


@pytest.mark.parametrize('existing_template_names, expected_name', (
    (
        ['Two week reminder'],
        'Two week reminder (copy)'
    ),
    (
        ['Two week reminder (copy)'],
        'Two week reminder (copy 2)'
    ),
    (
        ['Two week reminder', 'Two week reminder (copy)'],
        'Two week reminder (copy 2)'
    ),
    (
        ['Two week reminder (copy 8)', 'Two week reminder (copy 9)'],
        'Two week reminder (copy 10)'
    ),
    (
        ['Two week reminder (copy)', 'Two week reminder (copy 9)'],
        'Two week reminder (copy 10)'
    ),
    (
        ['Two week reminder (copy)', 'Two week reminder (copy 10)'],
        'Two week reminder (copy 2)'
    ),
))
def test_load_edit_template_with_copy_of_template(
    client_request,
    active_user_with_permission_to_two_services,
    mock_get_service_templates,
    mock_get_service_email_template,
    mock_get_non_empty_organisations_and_services_for_user,
    existing_template_names,
    expected_name,
):
    mock_get_service_templates.side_effect = lambda service_id: {'data': [
        {'name': existing_template_name, 'template_type': 'sms'}
        for existing_template_name in existing_template_names
    ]}
    client_request.login(active_user_with_permission_to_two_services)
    page = client_request.get(
        'main.copy_template',
        service_id=SERVICE_ONE_ID,
        template_id=TEMPLATE_ONE_ID,
        from_service=SERVICE_TWO_ID,
    )

    assert page.select_one('form')['method'] == 'post'

    assert page.select_one('input')['value'] == (
        expected_name
    )
    assert page.select_one('textarea').text == (
        'Your ((thing)) is due soon'
    )
    mock_get_service_email_template.assert_called_once_with(
        SERVICE_TWO_ID,
        TEMPLATE_ONE_ID,
    )


def test_cant_copy_template_from_non_member_service(
    client_request,
    mock_get_service_email_template,
    mock_get_organisations_and_services_for_user,
):
    client_request.get(
        'main.copy_template',
        service_id=SERVICE_ONE_ID,
        template_id=TEMPLATE_ONE_ID,
        from_service=SERVICE_TWO_ID,
        _expected_status=403,
    )
    assert mock_get_service_email_template.call_args_list == []


@pytest.mark.parametrize('endpoint, data, expected_error', (
    (
        'main.add_template_by_type',
        {
            'template_type': 'email',
        },
        "Sending emails has been disabled for your service."
    ),
    (
        'main.add_template_by_type',
        {
            'template_type': 'sms',
        },
        "Sending text messages has been disabled for your service."
    ),
    (
        'main.choose_template',
        {
            'operation': 'add-new-template',
            'add_template_by_template_type': 'email',
        },
        "Sending emails has been disabled for your service."
    ),
    (
        'main.choose_template',
        {
            'operation': 'add-new-template',
            'add_template_by_template_type': 'sms',
        },
        "Sending text messages has been disabled for your service."
    ),
))
def test_should_not_allow_creation_of_template_through_form_without_correct_permission(
    client_request,
    service_one,
    mock_get_service_templates,
    mock_get_template_folders,
    mock_get_organisations_and_services_for_user,
    endpoint,
    data,
    expected_error,
):
    service_one['permissions'] = ['edit_folders']
    page = client_request.post(
        endpoint,
        service_id=SERVICE_ONE_ID,
        _data=data,
        _follow_redirects=True,
    )
    assert normalize_spaces(page.select('main p')[0].text) == expected_error
    assert page.select(".page-footer-back-link")[0].text == "Back to add new template"
    assert page.select(".page-footer-back-link")[0]['href'] == url_for(
        '.add_template_by_type',
        service_id=service_one['id'],
        template_id='0',
    )


@pytest.mark.parametrize('type_of_template', ['email', 'sms'])
def test_should_not_allow_creation_of_a_template_without_correct_permission(
    logged_in_client,
    service_one,
    mocker,
    type_of_template,
):
    service_one['permissions'] = []
    template_description = {'sms': 'text messages', 'email': 'emails'}

    response = logged_in_client.get(url_for(
        '.add_service_template',
        service_id=service_one['id'],
        template_type=type_of_template),
        follow_redirects=True)

    page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')

    assert response.status_code == 200
    assert page.select('main p')[0].text.strip() == \
        "Sending {} has been disabled for your service.".format(template_description[type_of_template])
    assert page.select(".page-footer-back-link")[0].text == "Back to templates"
    assert page.select(".page-footer-back-link")[0]['href'] == url_for(
        '.choose_template',
        service_id=service_one['id'],
        template_id='0',
    )


@pytest.mark.parametrize('fixture,  expected_status_code', [
    (mock_get_service_email_template, 200),
    (mock_get_service_template, 200),
    (mock_get_service_letter_template, 302),
])
def test_should_redirect_to_one_off_if_template_type_is_letter(
    logged_in_client,
    active_user_with_permissions,
    multiple_reply_to_email_addresses,
    multiple_sms_senders,
    service_one,
    fake_uuid,
    mocker,
    fixture,
    expected_status_code
):
    fixture(mocker)

    page = logged_in_client.get(
        url_for('.set_sender', service_id=service_one['id'], template_id=fake_uuid)
    )

    assert page.status_code == expected_status_code


def test_should_redirect_when_saving_a_template(
    logged_in_client,
    active_user_with_permissions,
    mocker,
    mock_get_service_template,
    mock_update_service_template,
    fake_uuid,
):
    service = create_sample_service(active_user_with_permissions)
    mocker.patch('app.user_api_client.get_users_for_service', return_value=[active_user_with_permissions])
    template_id = fake_uuid
    name = "new name"
    content = "template <em>content</em> with & entity"
    data = {
        'id': template_id,
        'name': name,
        'template_content': content,
        'template_type': 'sms',
        'service': service['id'],
        'process_type': 'normal'
    }
    response = logged_in_client.post(url_for(
        '.edit_service_template',
        service_id=service['id'],
        template_id=template_id), data=data)

    assert response.status_code == 302
    assert response.location == url_for(
        '.view_template', service_id=service['id'], template_id=template_id, _external=True)
    mock_update_service_template.assert_called_with(
        template_id, name, 'sms', content, service['id'], None, 'normal', postage=None)


def test_should_edit_content_when_process_type_is_priority_not_platform_admin(
    logged_in_client,
    active_user_with_permissions,
    mocker,
    mock_get_service_template_with_priority,
    mock_update_service_template,
    fake_uuid,
):
    service = create_sample_service(active_user_with_permissions)
    mocker.patch('app.user_api_client.get_users_for_service', return_value=[active_user_with_permissions])
    template_id = fake_uuid
    data = {
        'id': template_id,
        'name': "new name",
        'template_content': "new template <em>content</em> with & entity",
        'template_type': 'sms',
        'service': service['id'],
        'process_type': 'priority'
    }
    response = logged_in_client.post(url_for(
        '.edit_service_template',
        service_id=service['id'],
        template_id=template_id), data=data)
    assert response.status_code == 302
    assert response.location == url_for(
        '.view_template', service_id=service['id'], template_id=template_id, _external=True)
    mock_update_service_template.assert_called_with(
        template_id,
        "new name",
        'sms',
        "new template <em>content</em> with & entity",
        service['id'],
        None,
        'priority',
        postage=None
    )


def test_should_not_allow_template_edits_without_correct_permission(
    logged_in_client,
    mock_get_service_template,
    service_one,
    fake_uuid,
):
    template_id = fake_uuid
    service_one['permissions'] = ['email']

    response = logged_in_client.get(url_for(
        '.edit_service_template',
        service_id=service_one['id'],
        template_id=template_id),
        follow_redirects=True)
    page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')

    assert response.status_code == 200
    assert page.select('main p')[0].text.strip() == "Sending text messages has been disabled for your service."
    assert page.select(".page-footer-back-link")[0].text == "Back to the template"
    assert page.select(".page-footer-back-link")[0]['href'] == url_for(
        '.view_template',
        service_id=service_one['id'],
        template_id=template_id,
    )


def test_should_403_when_edit_template_with_process_type_of_priority_for_non_platform_admin(
    client,
    active_user_with_permissions,
    mocker,
    mock_get_service_template,
    mock_update_service_template,
    fake_uuid,
):
    service = create_sample_service(active_user_with_permissions)
    client.login(active_user_with_permissions, mocker, service)
    mocker.patch('app.user_api_client.get_users_for_service', return_value=[active_user_with_permissions])
    template_id = fake_uuid
    data = {
        'id': template_id,
        'name': "new name",
        'template_content': "template <em>content</em> with & entity",
        'template_type': 'sms',
        'service': service['id'],
        'process_type': 'priority'
    }
    response = client.post(url_for(
        '.edit_service_template',
        service_id=service['id'],
        template_id=template_id), data=data)
    assert response.status_code == 403
    mock_update_service_template.called == 0


def test_should_403_when_create_template_with_process_type_of_priority_for_non_platform_admin(
    client,
    active_user_with_permissions,
    mocker,
    mock_get_service_template,
    mock_update_service_template,
    fake_uuid,
):
    service = create_sample_service(active_user_with_permissions)
    client.login(active_user_with_permissions, mocker, service)
    mocker.patch('app.user_api_client.get_users_for_service', return_value=[active_user_with_permissions])
    template_id = fake_uuid
    data = {
        'id': template_id,
        'name': "new name",
        'template_content': "template <em>content</em> with & entity",
        'template_type': 'sms',
        'service': service['id'],
        'process_type': 'priority'
    }
    response = client.post(url_for(
        '.add_service_template',
        service_id=service['id'],
        template_type='sms'), data=data)
    assert response.status_code == 403
    mock_update_service_template.called == 0


@pytest.mark.parametrize('template_mock, template_type, expected_paragraphs', [
    (
        mock_get_service_email_template,
        "email",
        [
            'You removed ((date))',
            'You added ((name))',
            'When you send messages using this template you’ll need 3 columns of data:',
        ]
    ),
    (
        mock_get_service_letter_template,
        "letter",
        [
            'You removed ((date))',
            'You added ((name))',
            'When you send messages using this template you’ll need 9 columns of data:',
        ]
    ),
])
def test_should_show_interstitial_when_making_breaking_change(
    logged_in_client,
    api_user_active,
    mock_login,
    mock_update_service_template,
    mock_get_user,
    mock_get_service,
    mock_get_user_by_email,
    mock_has_permissions,
    fake_uuid,
    mocker,
    template_mock,
    template_type,
    expected_paragraphs,
):
    template_mock(
        mocker,
        subject="Your ((thing)) is due soon",
        content="Your vehicle tax expires on ((date))",
    )
    service_id = fake_uuid
    template_id = fake_uuid
    data = {
        'id': template_id,
        'name': "new name",
        'template_content': "hello lets talk about ((thing))",
        'template_type': template_type,
        'subject': 'reminder \'" <span> & ((name))',
        'service': service_id,
        'process_type': 'normal'
    }

    if template_type == "letter":
        data["postage"] = 'None'

    response = logged_in_client.post(
        url_for('.edit_service_template', service_id=service_id, template_id=template_id),
        data=data
    )

    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
    assert page.h1.string.strip() == "Confirm changes"
    assert page.find('a', {'class': 'page-footer-back-link'})['href'] == url_for(".edit_service_template",
                                                                                 service_id=service_id,
                                                                                 template_id=template_id)
    for index, p in enumerate(expected_paragraphs):
        assert normalize_spaces(page.select('main p')[index].text) == p

    for key, value in {
        'name': 'new name',
        'subject': 'reminder \'" <span> & ((name))',
        'template_content': 'hello lets talk about ((thing))',
        'confirm': 'true'
    }.items():
        assert page.find('input', {'name': key})['value'] == value

    # BeautifulSoup returns the value attribute as unencoded, let’s make
    # sure that it is properly encoded in the HTML
    assert str(page.find('input', {'name': 'subject'})) == (
        """<input name="subject" type="hidden" value="reminder '&quot; &lt;span&gt; &amp; ((name))"/>"""
    )


def test_removing_placeholders_is_not_a_breaking_change(
    logged_in_client,
    mock_get_service_email_template,
    mock_update_service_template,
    mock_has_permissions,
    fake_uuid,
):
    service_id = fake_uuid
    template_id = fake_uuid
    existing_template = mock_get_service_email_template(0, 0)['data']
    response = logged_in_client.post(
        url_for(
            '.edit_service_template',
            service_id=service_id,
            template_id=template_id
        ),
        data={
            'name': existing_template['name'],
            'template_content': "no placeholders",
            'subject': existing_template['subject'],
        }
    )

    assert response.status_code == 302
    assert response.location == url_for(
        'main.view_template',
        service_id=service_id,
        template_id=template_id,
        _external=True,
    )


def test_should_not_create_too_big_template(
    logged_in_client,
    service_one,
    mock_get_service_template,
    mock_create_service_template_content_too_big,
    fake_uuid,
):
    template_type = 'sms'
    data = {
        'name': "new name",
        'template_content': "template content",
        'template_type': template_type,
        'service': service_one['id'],
        'process_type': 'normal'
    }
    resp = logged_in_client.post(url_for(
        '.add_service_template',
        service_id=service_one['id'],
        template_type=template_type
    ), data=data)

    assert resp.status_code == 200
    assert "Content has a character count greater than the limit of 459" in resp.get_data(as_text=True)


def test_should_not_update_too_big_template(
    logged_in_client,
    service_one,
    mock_get_service_template,
    mock_update_service_template_400_content_too_big,
    fake_uuid,
):
    template_id = fake_uuid
    data = {
        'id': fake_uuid,
        'name': "new name",
        'template_content': "template content",
        'service': service_one['id'],
        'template_type': 'sms',
        'process_type': 'normal'
    }
    resp = logged_in_client.post(url_for(
        '.edit_service_template',
        service_id=service_one['id'],
        template_id=template_id), data=data)

    assert resp.status_code == 200
    assert "Content has a character count greater than the limit of 459" in resp.get_data(as_text=True)


def test_should_redirect_when_saving_a_template_email(
    logged_in_client,
    api_user_active,
    mock_login,
    mock_get_service_email_template,
    mock_update_service_template,
    mock_get_user,
    mock_get_service,
    mock_get_user_by_email,
    mock_has_permissions,
    fake_uuid,
):
    service_id = fake_uuid
    template_id = fake_uuid
    name = "new name"
    content = "template <em>content</em> with & entity ((thing)) ((date))"
    subject = "subject & entity"
    data = {
        'id': template_id,
        'name': name,
        'template_content': content,
        'template_type': 'email',
        'service': service_id,
        'subject': subject,
        'process_type': 'normal'
    }
    response = logged_in_client.post(url_for(
        '.edit_service_template',
        service_id=service_id,
        template_id=template_id), data=data)
    assert response.status_code == 302
    assert response.location == url_for(
        '.view_template',
        service_id=service_id,
        template_id=template_id,
        _external=True)
    mock_update_service_template.assert_called_with(
        template_id, name, 'email', content, service_id, subject, 'normal', postage=None)


def test_should_show_delete_template_page_with_time_block(
    client_request,
    mock_get_service_template,
    mock_get_template_folders,
    mocker,
    fake_uuid
):
    with freeze_time('2012-01-01 12:00:00'):
        template = template_json('1234', '1234', "Test template", "sms", "Something very interesting")
        notification = single_notification_json('1234', template=template)

        mocker.patch('app.template_statistics_client.get_template_statistics_for_template',
                     return_value=notification)

    with freeze_time('2012-01-01 12:10:00'):
        page = client_request.get(
            '.delete_service_template',
            service_id=SERVICE_ONE_ID,
            template_id=fake_uuid,
            _test_page_title=False,
        )
    assert "Are you sure you want to delete ‘Two week reminder’?" in page.select('.banner-dangerous')[0].text
    assert normalize_spaces(page.select('.banner-dangerous p')[0].text) == (
        'This template was last used 10 minutes ago.'
    )
    assert normalize_spaces(page.select('.sms-message-wrapper')[0].text) == (
        'service one: Template <em>content</em> with & entity'
    )
    mock_get_service_template.assert_called_with(SERVICE_ONE_ID, fake_uuid)


def test_should_show_delete_template_page_with_time_block_for_empty_notification(
    client_request,
    mock_get_service_template,
    mock_get_template_folders,
    mocker,
    fake_uuid
):
    with freeze_time('2012-01-08 12:00:00'):
        template = template_json('1234', '1234', "Test template", "sms", "Something very interesting")
        single_notification_json('1234', template=template)
        mocker.patch('app.template_statistics_client.get_template_statistics_for_template',
                     return_value=None)

    with freeze_time('2012-01-01 11:00:00'):
        page = client_request.get(
            '.delete_service_template',
            service_id=SERVICE_ONE_ID,
            template_id=fake_uuid,
            _test_page_title=False,
        )
    assert "Are you sure you want to delete ‘Two week reminder’?" in page.select('.banner-dangerous')[0].text
    assert normalize_spaces(page.select('.banner-dangerous p')[0].text) == (
        'This template was last used more than seven days ago.'
    )
    assert normalize_spaces(page.select('.sms-message-wrapper')[0].text) == (
        'service one: Template <em>content</em> with & entity'
    )
    mock_get_service_template.assert_called_with(SERVICE_ONE_ID, fake_uuid)


def test_should_show_delete_template_page_with_never_used_block(
    client_request,
    mock_get_service_template,
    mock_get_template_folders,
    fake_uuid,
    mocker,
):
    mocker.patch(
        'app.template_statistics_client.get_template_statistics_for_template',
        side_effect=HTTPError(response=Mock(status_code=404), message="Default message")
    )
    page = client_request.get(
        '.delete_service_template',
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _test_page_title=False,
    )
    assert "Are you sure you want to delete ‘Two week reminder’?" in page.select('.banner-dangerous')[0].text
    assert not page.select('.banner-dangerous p')
    assert normalize_spaces(page.select('.sms-message-wrapper')[0].text) == (
        'service one: Template <em>content</em> with & entity'
    )
    mock_get_service_template.assert_called_with(SERVICE_ONE_ID, fake_uuid)


def test_should_redirect_when_deleting_a_template(
    logged_in_client,
    api_user_active,
    mock_login,
    mock_get_service,
    mock_get_service_template,
    mock_delete_service_template,
    mock_get_user,
    mock_get_user_by_email,
    mock_has_permissions,
    fake_uuid,
):
    service_id = fake_uuid
    template_id = fake_uuid
    name = "new name"
    type_ = "sms"
    content = "template content"
    data = {
        'id': str(template_id),
        'name': name,
        'template_type': type_,
        'content': content,
        'service': service_id
    }
    response = logged_in_client.post(url_for(
        '.delete_service_template',
        service_id=service_id,
        template_id=template_id
    ), data=data)

    assert response.status_code == 302
    assert response.location == url_for(
        '.choose_template',
        service_id=service_id, _external=True)
    mock_get_service_template.assert_called_with(
        service_id, template_id)
    mock_delete_service_template.assert_called_with(
        service_id, template_id)


@freeze_time('2016-01-01T15:00')
def test_should_show_page_for_a_deleted_template(
    logged_in_client,
    api_user_active,
    mock_login,
    mock_get_service,
    mock_get_template_folders,
    mock_get_deleted_template,
    single_letter_contact_block,
    mock_get_user,
    mock_get_user_by_email,
    mock_has_permissions,
    fake_uuid,
):
    service_id = fake_uuid
    template_id = fake_uuid
    response = logged_in_client.get(url_for(
        '.view_template',
        service_id=service_id,
        template_id=template_id
    ))

    assert response.status_code == 200

    content = response.get_data(as_text=True)
    page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
    assert url_for("main.edit_service_template", service_id=fake_uuid, template_id=fake_uuid) not in content
    assert url_for("main.send_test", service_id=fake_uuid, template_id=fake_uuid) not in content
    assert page.select('p.hint')[0].text.strip() == 'This template was deleted today at 3:00pm.'
    assert 'Delete this template' not in page.select_one('main').text

    mock_get_deleted_template.assert_called_with(service_id, template_id)


@pytest.mark.parametrize('route', [
    'main.add_service_template',
    'main.edit_service_template',
    'main.delete_service_template'
])
def test_route_permissions(
    route,
    mocker,
    app_,
    client,
    api_user_active,
    service_one,
    mock_get_service_template,
    mock_get_template_folders,
    mock_get_template_statistics_for_template,
    fake_uuid,
):
    validate_route_permission(
        mocker,
        app_,
        "GET",
        200,
        url_for(
            route,
            service_id=service_one['id'],
            template_type='sms',
            template_id=fake_uuid),
        ['manage_templates'],
        api_user_active,
        service_one)


def test_route_permissions_for_choose_template(
    mocker,
    app_,
    client,
    api_user_active,
    mock_get_template_folders,
    service_one,
    mock_get_service_templates
):
    mocker.patch('app.job_api_client.get_job')
    validate_route_permission(
        mocker,
        app_,
        "GET",
        200,
        url_for(
            'main.choose_template',
            service_id=service_one['id'],
        ),
        [],
        api_user_active,
        service_one)


@pytest.mark.parametrize('route', [
    'main.add_service_template',
    'main.edit_service_template',
    'main.delete_service_template'
])
def test_route_invalid_permissions(
    route,
    mocker,
    app_,
    client,
    api_user_active,
    service_one,
    mock_get_service_template,
    mock_get_template_statistics_for_template,
    fake_uuid,
):
    validate_route_permission(
        mocker,
        app_,
        "GET",
        403,
        url_for(
            route,
            service_id=service_one['id'],
            template_type='sms',
            template_id=fake_uuid),
        ['view_activity'],
        api_user_active,
        service_one)


def test_get_last_use_message_returns_no_template_message():
    assert get_last_use_message('My Template', []) == 'My Template has never been used'


@freeze_time('2000-01-01T15:00')
def test_get_last_use_message_uses_most_recent_statistics():
    template_statistics = [
        {
            'updated_at': '2000-01-01T12:00:00.000000+00:00'
        },
        {
            'updated_at': '2000-01-01T09:00:00.000000+00:00'
        },
    ]
    assert get_last_use_message('My Template', template_statistics) == 'My Template was last used 3 hours ago'


@pytest.mark.parametrize('from_time, until_time, message', [
    (datetime(2000, 1, 1, 12, 0), datetime(2000, 1, 1, 12, 0, 59), 'under a minute'),
    (datetime(2000, 1, 1, 12, 0), datetime(2000, 1, 1, 12, 1), '1 minute'),
    (datetime(2000, 1, 1, 12, 0), datetime(2000, 1, 1, 12, 2, 35), '2 minutes'),
    (datetime(2000, 1, 1, 12, 0), datetime(2000, 1, 1, 12, 59), '59 minutes'),
    (datetime(2000, 1, 1, 12, 0), datetime(2000, 1, 1, 13, 0), '1 hour'),
    (datetime(2000, 1, 1, 12, 0), datetime(2000, 1, 1, 14, 0), '2 hours'),
    (datetime(2000, 1, 1, 12, 0), datetime(2000, 1, 2, 11, 59), '23 hours'),
    (datetime(2000, 1, 1, 12, 0), datetime(2000, 1, 2, 12, 0), '1 day'),
    (datetime(2000, 1, 1, 12, 0), datetime(2000, 1, 3, 14, 0), '2 days'),
])
def test_get_human_readable_delta(from_time, until_time, message):
    assert get_human_readable_delta(from_time, until_time) == message


def test_can_create_email_template_with_emoji(
    logged_in_client,
    service_one,
    mock_create_service_template
):
    data = {
        'name': "new name",
        'subject': "Food incoming!",
        'template_content': "here's a burrito 🌯",
        'template_type': 'email',
        'service': service_one['id'],
        'process_type': 'normal'
    }
    resp = logged_in_client.post(url_for(
        '.add_service_template',
        service_id=service_one['id'],
        template_type='email'
    ), data=data)

    assert resp.status_code == 302


def test_should_not_create_sms_template_with_emoji(
    logged_in_client,
    service_one,
    mock_create_service_template
):
    data = {
        'name': "new name",
        'template_content': "here are some noodles 🍜",
        'template_type': 'sms',
        'service': service_one['id'],
        'process_type': 'normal'
    }
    resp = logged_in_client.post(url_for(
        '.add_service_template',
        service_id=service_one['id'],
        template_type='sms'
    ), data=data)

    assert resp.status_code == 200
    assert "You can’t use 🍜 in text messages." in resp.get_data(as_text=True)


def test_should_not_update_sms_template_with_emoji(
    logged_in_client,
    service_one,
    mock_get_service_template,
    mock_update_service_template,
    fake_uuid,
):
    data = {
        'id': fake_uuid,
        'name': "new name",
        'template_content': "here's a burger 🍔",
        'service': service_one['id'],
        'template_type': 'sms',
        'process_type': 'normal'
    }
    resp = logged_in_client.post(url_for(
        '.edit_service_template',
        service_id=service_one['id'],
        template_id=fake_uuid), data=data)

    assert resp.status_code == 200
    assert "You can’t use 🍔 in text messages." in resp.get_data(as_text=True)


def test_should_create_sms_template_without_downgrading_unicode_characters(
    logged_in_client,
    service_one,
    mock_create_service_template
):
    msg = 'here:\tare some “fancy quotes” and non\u200Bbreaking\u200Bspaces'

    data = {
        'name': "new name",
        'template_content': msg,
        'template_type': 'sms',
        'service': service_one['id'],
        'process_type': 'normal'
    }
    resp = logged_in_client.post(url_for(
        '.add_service_template',
        service_id=service_one['id'],
        template_type='sms'
    ), data=data)

    mock_create_service_template.assert_called_with(
        ANY,  # name
        ANY,  # type
        msg,  # content
        ANY,  # service_id
        ANY,  # subject
        ANY,  # process_type
        ANY,  # parent_folder_id
    )
    assert resp.status_code == 302


def test_should_show_template_as_first_page_of_tour(
    client_request,
    mock_get_service_template,
    service_one,
    fake_uuid,
):

    page = client_request.get(
        'main.start_tour',
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
    )

    assert normalize_spaces(
        page.select('.banner-tour .heading-medium')[0].text
    ) == (
        'Try sending yourself this example'
    )

    assert normalize_spaces(
        page.select('.sms-message-wrapper')[0].text
    ) == (
        'service one: Template <em>content</em> with & entity'
    )

    assert page.select('a.button')[0]['href'] == url_for(
        '.send_test', service_id=SERVICE_ONE_ID, template_id=fake_uuid, help=2
    )


@pytest.mark.parametrize('template_mock', [
    mock_get_service_email_template,
    mock_get_service_letter_template,
])
def test_cant_see_email_template_in_tour(
    client_request,
    fake_uuid,
    mocker,
    template_mock,
):

    template_mock(mocker)

    client_request.get(
        'main.start_tour',
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _expected_status=404,
    )


def test_should_show_message_before_redacting_template(
    client_request,
    mock_get_service_template,
    service_one,
    fake_uuid,
):

    page = client_request.get(
        'main.redact_template',
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _test_page_title=False,
    )

    assert (
        'Are you sure you want to hide personalisation after sending?'
    ) in page.select('.banner-dangerous')[0].text

    form = page.select('.banner-dangerous form')[0]

    assert 'action' not in form
    assert form['method'] == 'post'


def test_should_show_redact_template(
    client_request,
    mock_get_service_template,
    mock_get_template_folders,
    mock_redact_template,
    single_letter_contact_block,
    service_one,
    fake_uuid,
):

    page = client_request.post(
        'main.redact_template',
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _follow_redirects=True,
    )

    assert normalize_spaces(page.select('.banner-default-with-tick')[0].text) == (
        'Personalised content will be hidden for messages sent with this template'
    )

    mock_redact_template.assert_called_once_with(SERVICE_ONE_ID, fake_uuid)


def test_should_show_hint_once_template_redacted(
    client_request,
    mocker,
    service_one,
    mock_get_template_folders,
    fake_uuid,
):

    mock_get_service_email_template(mocker, redact_personalisation=True)

    page = client_request.get(
        'main.view_template',
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
    )

    assert page.select('.hint')[0].text == 'Personalisation is hidden after sending'


def test_should_not_show_redaction_stuff_for_letters(
    client_request,
    mocker,
    fake_uuid,
    mock_get_service_letter_template,
    mock_get_template_folders,
    single_letter_contact_block,
):

    mocker.patch('app.main.views.templates.get_page_count_for_letter', return_value=1)

    page = client_request.get(
        'main.view_template',
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
    )

    assert page.select('.hint') == []
    assert 'personalisation' not in ' '.join(
        link.text.lower() for link in page.select('a')
    )


def test_set_template_sender(
    client_request,
    fake_uuid,
    mock_update_service_template_sender,
    mock_get_service_letter_template,
    single_letter_contact_block
):
    data = {
        'sender': '1234',
    }

    client_request.post(
        'main.set_template_sender',
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _data=data,
    )

    mock_update_service_template_sender.assert_called_once_with(
        SERVICE_ONE_ID,
        fake_uuid,
        '1234',
    )


@pytest.mark.parametrize('fixture, add_button_is_on_page', [
    (no_letter_contact_blocks, True),
    (single_letter_contact_block, False),
])
def test_add_sender_link_only_appears_on_services_with_no_senders(
    client_request,
    fake_uuid,
    mocker,
    fixture,
    add_button_is_on_page,
    mock_get_service_letter_template,
    no_letter_contact_blocks
):
    fixture(mocker)
    page = client_request.get(
        'main.set_template_sender',
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
    )

    assert (page.select_one('.column-three-quarters form > a') is not None) == add_button_is_on_page
