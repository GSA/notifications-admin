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


@pytest.mark.parametrize('extra_permissions', (
    pytest.param(
        [],
        marks=pytest.mark.xfail(raises=AssertionError),
    ),
    pytest.param(
        ['upload_letters'],
        marks=pytest.mark.xfail(raises=AssertionError),
    ),
    ['letter'],
    ['letter', 'upload_letters'],
))
def test_upload_letters_button_only_with_letters_permission(
    client_request,
    service_one,
    mock_get_uploads,
    mock_get_jobs,
    mock_get_no_contact_lists,
    extra_permissions,
):
    service_one['permissions'] += extra_permissions
    page = client_request.get('main.uploads', service_id=SERVICE_ONE_ID)
    assert page.find('a', text=re.compile('Upload a letter'))


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
    (['letter'], (
        'You have not uploaded any files recently. '
        'Upload a letter and Notify will print, pack and post it for you.'
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


@pytest.mark.skip(reason="Needs to be rewritten with no letters")
@freeze_time('2017-10-10 10:10:10')
def test_get_upload_hub_page(
    mocker,
    client_request,
    service_one,
    mock_get_uploads,
    mock_get_no_contact_lists,
):
    mocker.patch('app.job_api_client.get_jobs', return_value={'data': []})
    service_one['permissions'] += ['letter', 'upload_letters']
    page = client_request.get('main.uploads', service_id=SERVICE_ONE_ID)
    assert page.find('h1').text == 'Uploads'
    assert page.find('a', text=re.compile('Upload a letter')).attrs['href'] == url_for(
        'main.upload_letter', service_id=SERVICE_ONE_ID
    )

    uploads = page.select('tbody tr')

    assert len(uploads) == 3

    assert normalize_spaces(uploads[0].text.strip()) == (
        'Uploaded letters '
        'Printing today at 5:30pm '
        '33 letters'
    )
    assert uploads[0].select_one('a.file-list-filename-large')['href'] == url_for(
        'main.uploaded_letters',
        service_id=SERVICE_ONE_ID,
        letter_print_day='2017-10-10',
    )

    assert normalize_spaces(uploads[1].text.strip()) == (
        'some.csv '
        'Sent 1 January 2016 at 11:09am '
        '0 sending 8 delivered 2 failed'
    )
    assert uploads[1].select_one('a.file-list-filename-large')['href'] == (
        '/services/{}/jobs/job_id_1'.format(SERVICE_ONE_ID)
    )

    assert normalize_spaces(uploads[2].text.strip()) == (
        'some.pdf '
        'Sent 1 January 2016 at 11:09am '
        'Firstname Lastname '
        '123 Example Street'
    )
    assert normalize_spaces(str(uploads[2].select_one('.govuk-body'))) == (
        '<p class="govuk-body letter-recipient-summary"> '
        'Firstname Lastname<br/> '
        '123 Example Street<br/> '
        '</p>'
    )
    assert uploads[2].select_one('a.file-list-filename-large')['href'] == (
        '/services/{}/notification/letter_id_1'.format(SERVICE_ONE_ID)
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
            'Sending 1 January 2016 at 11:09pm '
            '1 text message waiting to send'
        ),
        (
            'send_me_later.csv '
            'Sending 1 January 2016 at 11:09am '
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
            'Sending 1 January 2016 at 11:09pm '
            '1 text message waiting to send'
        ),
        (
            'send_me_later.csv '
            'Sending 1 January 2016 at 11:09am '
            '1 text message waiting to send'
        ),
    ]
    assert page.select_one('.file-list-filename-large')['href'] == url_for(
        'main.contact_list',
        service_id=SERVICE_ONE_ID,
        contact_list_id='d7b0bd1a-d1c7-4621-be5c-3c1b4278a2ad',
    )


def test_get_uploads_shows_pagination(
    client_request,
    active_user_with_permissions,
    mock_get_jobs,
    mock_get_uploads,
    mock_get_no_contact_lists,
):
    page = client_request.get('main.uploads', service_id=SERVICE_ONE_ID)

    assert normalize_spaces(page.select_one('.next-page').text) == (
        'Next page '
        'page 2'
    )
    assert normalize_spaces(page.select_one('.previous-page').text) == (
        'Previous page '
        'page 0'
    )
