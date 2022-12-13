import re

import pytest
from flask import url_for
from freezegun import freeze_time

from app.formatters import normalize_spaces
from tests.conftest import (
    SERVICE_ONE_ID,
    create_active_caseworking_user,
    create_active_user_with_permissions,
    create_platform_admin_user,
)


@pytest.mark.skip(reason="Not sure that TTS needs this")
@pytest.mark.parametrize('user', (
    create_platform_admin_user(),
    create_active_user_with_permissions(),
))
def test_all_users_have_upload_contact_list(
    client_request,
    mock_get_uploads,
    mock_get_jobs,
    mock_get_no_contact_lists,
    user,
):
    client_request.login(user)
    page = client_request.get('main.uploads', service_id=SERVICE_ONE_ID)
    button = page.find('a', text=re.compile('Upload an emergency contact list'))
    assert button
    assert button['href'] == url_for(
        'main.upload_contact_list', service_id=SERVICE_ONE_ID,
    )


@pytest.mark.parametrize('extra_permissions, expected_empty_message', (
    ([], (
        'You have not uploaded any files recently.'
    )),
))
def test_get_upload_hub_with_no_uploads(
    mocker,
    client_request,
    service_one,
    mock_get_no_uploads,
    mock_get_no_contact_lists,
    extra_permissions,
    expected_empty_message,
):
    mocker.patch('app.job_api_client.get_jobs', return_value={'data': []})
    service_one['permissions'] += extra_permissions
    page = client_request.get('main.uploads', service_id=SERVICE_ONE_ID)
    assert normalize_spaces(' '.join(
        paragraph.text for paragraph in page.select('main p')
    )) == expected_empty_message
    assert not page.select('.file-list-filename')


@freeze_time('2017-10-10 10:10:10')
def test_get_upload_hub_page(
    mocker,
    client_request,
    service_one,
    mock_get_uploads,
    mock_get_no_contact_lists,
):
    mocker.patch('app.job_api_client.get_jobs', return_value={'data': []})
    page = client_request.get('main.uploads', service_id=SERVICE_ONE_ID)
    assert page.find('h1').text == 'Uploads'

    uploads = page.select('tbody tr')

    assert len(uploads) == 1

    assert normalize_spaces(uploads[0].text.strip()) == (
        'some.csv '
        'Sent 1 January 2016 at 6:09am '
        '0 sending 8 delivered 2 failed'
    )
    assert uploads[0].select_one('a.file-list-filename-large')['href'] == (
        '/services/{}/jobs/job_id_1'.format(SERVICE_ONE_ID)
    )


@pytest.mark.parametrize('user', (
    create_active_caseworking_user(),
    create_active_user_with_permissions(),
))
@freeze_time("2012-12-12 12:12")
def test_uploads_page_shows_scheduled_jobs(
    mocker,
    client_request,
    mock_get_no_uploads,
    mock_get_jobs,
    mock_get_no_contact_lists,
    user,
):
    client_request.login(user)
    page = client_request.get('main.uploads', service_id=SERVICE_ONE_ID)

    assert [
        normalize_spaces(row.text) for row in page.select('tr')
    ] == [
        (
            'File Status'
        ),
        (
            'even_later.csv '
            'Sending 1 January 2016 at 6:09pm '
            '1 text message waiting to send'
        ),
        (
            'send_me_later.csv '
            'Sending 1 January 2016 at 6:09am '
            '1 text message waiting to send'
        ),
    ]
    assert not page.select('.table-empty-message')


@freeze_time('2020-03-15')
def test_uploads_page_shows_contact_lists_first(
    mocker,
    client_request,
    mock_get_no_uploads,
    mock_get_jobs,
    mock_get_contact_lists,
    mock_get_service_data_retention,
):
    page = client_request.get('main.uploads', service_id=SERVICE_ONE_ID)

    assert [
        normalize_spaces(row.text) for row in page.select('tr')
    ] == [
        (
            'File Status'
        ),
        (
            'phone number list.csv '
            'Used twice in the last 7 days '
            '123 saved phone numbers'
        ),
        (
            'EmergencyContactList.xls '
            'Not used in the last 7 days '
            '100 saved email addresses'
        ),
        (
            'UnusedList.tsv '
            'Not used yet '
            '1 saved phone number'
        ),
        (
            'even_later.csv '
            'Sending 1 January 2016 at 6:09pm '
            '1 text message waiting to send'
        ),
        (
            'send_me_later.csv '
            'Sending 1 January 2016 at 6:09am '
            '1 text message waiting to send'
        ),
    ]
    assert page.select_one('.file-list-filename-large')['href'] == url_for(
        'main.contact_list',
        service_id=SERVICE_ONE_ID,
        contact_list_id='d7b0bd1a-d1c7-4621-be5c-3c1b4278a2ad',
    )
