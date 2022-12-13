from collections import namedtuple
from unittest.mock import call

import pytest

from app.s3_client import default_access_key, default_region, default_secret_key
from app.s3_client.s3_logo_client import (
    EMAIL_LOGO_LOCATION_STRUCTURE,
    TEMP_TAG,
    delete_email_temp_file,
    delete_email_temp_files_created_by,
    permanent_email_logo_name,
    persist_logo,
    upload_email_logo,
)

bucket = 'test_bucket'
bucket_credentials = {
    'bucket': bucket,
    'access_key_id': default_access_key,
    'secret_access_key': default_secret_key,
    'region': default_region
}
data = {'data': 'some_data'}
filename = 'test.png'
svg_filename = 'test.svg'
upload_id = 'test_uuid'
region = 'us-west-2'


@pytest.fixture
def upload_filename(fake_uuid):
    return EMAIL_LOGO_LOCATION_STRUCTURE.format(
        temp=TEMP_TAG.format(user_id=fake_uuid), unique_id=upload_id, filename=filename)


def test_upload_email_logo_calls_correct_args(client_request, mocker, fake_uuid, upload_filename):
    mocker.patch('uuid.uuid4', return_value=upload_id)
    mocker.patch.dict('flask.current_app.config', {'LOGO_UPLOAD_BUCKET': bucket_credentials})
    mocked_s3_upload = mocker.patch('app.s3_client.s3_logo_client.utils_s3upload')

    upload_email_logo(filename=filename, user_id=fake_uuid, filedata=data)

    mocked_s3_upload.assert_called_once_with(
        filedata=data,
        region=region,
        file_location=upload_filename,
        bucket_name=bucket,
        content_type='image/png',
        access_key=default_access_key,
        secret_key=default_secret_key,
    )


def test_persist_logo(client_request, mocker, fake_uuid, upload_filename):
    mocker.patch.dict('flask.current_app.config', {'LOGO_UPLOAD_BUCKET': bucket_credentials})
    mocked_get_s3_object = mocker.patch('app.s3_client.s3_logo_client.get_s3_object')
    mocked_delete_s3_object = mocker.patch('app.s3_client.s3_logo_client.delete_s3_object')

    new_filename = permanent_email_logo_name(upload_filename, fake_uuid)

    persist_logo(upload_filename, new_filename)

    mocked_get_s3_object.assert_called_once_with(
        bucket, new_filename, default_access_key, default_secret_key, default_region)
    mocked_delete_s3_object.assert_called_once_with(upload_filename)


def test_persist_logo_returns_if_not_temp(client_request, mocker, fake_uuid):
    filename = 'logo.png'
    persist_logo(filename, filename)

    mocked_get_s3_object = mocker.patch('app.s3_client.s3_logo_client.get_s3_object')
    mocked_delete_s3_object = mocker.patch('app.s3_client.s3_logo_client.delete_s3_object')

    assert mocked_get_s3_object.called is False
    assert mocked_delete_s3_object.called is False


def test_permanent_email_logo_name_removes_TEMP_TAG_from_filename(upload_filename, fake_uuid):
    new_name = permanent_email_logo_name(upload_filename, fake_uuid)

    assert new_name == 'test_uuid-test.png'


def test_permanent_email_logo_name_does_not_change_filenames_with_no_TEMP_TAG():
    filename = 'logo.png'
    new_name = permanent_email_logo_name(filename, filename)

    assert new_name == filename


def test_delete_email_temp_files_created_by_user(client_request, mocker, fake_uuid):
    obj = namedtuple("obj", ["key"])
    objs = [obj(key='test1'), obj(key='test2')]

    mocker.patch('app.s3_client.s3_logo_client.get_s3_objects_filter_by_prefix', return_value=objs)
    mocked_delete_s3_object = mocker.patch('app.s3_client.s3_logo_client.delete_s3_object')

    delete_email_temp_files_created_by(fake_uuid)

    for index, arg in enumerate(mocked_delete_s3_object.call_args_list):
        assert arg == call(objs[index].key)


def test_delete_single_email_temp_file(client_request, mocker, upload_filename):
    mocked_delete_s3_object = mocker.patch('app.s3_client.s3_logo_client.delete_s3_object')

    delete_email_temp_file(upload_filename)

    mocked_delete_s3_object.assert_called_with(upload_filename)


def test_does_not_delete_non_temp_email_file(client_request, mocker):
    filename = 'logo.png'
    mocked_delete_s3_object = mocker.patch('app.s3_client.s3_logo_client.delete_s3_object')

    with pytest.raises(ValueError) as error:
        delete_email_temp_file(filename)

    assert mocked_delete_s3_object.called is False
    assert str(error.value) == 'Not a temp file: {}'.format(filename)
