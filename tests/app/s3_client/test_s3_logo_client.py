from collections import namedtuple
from unittest.mock import call

import pytest

from app.s3_client.s3_logo_client import (
    EMAIL_LOGO_LOCATION_STRUCTURE,
    TEMP_TAG,
    delete_email_temp_file,
    delete_email_temp_files_created_by,
    permanent_email_logo_name,
    persist_logo,
    upload_email_logo,
)

data = {"data": "some_data"}
filename = "test.png"
svg_filename = "test.svg"
upload_id = "test_uuid"


@pytest.fixture()
def upload_filename(fake_uuid):
    return EMAIL_LOGO_LOCATION_STRUCTURE.format(
        temp=TEMP_TAG.format(user_id=fake_uuid), unique_id=upload_id, filename=filename
    )


@pytest.fixture()
def bucket_credentials(notify_admin):
    return notify_admin.config["LOGO_UPLOAD_BUCKET"]


def test_upload_email_logo_calls_correct_args(
    client_request, mocker, bucket_credentials, fake_uuid, upload_filename
):
    mocker.patch("uuid.uuid4", return_value=upload_id)
    mocked_s3_upload = mocker.patch("app.s3_client.s3_logo_client.utils_s3upload")

    upload_email_logo(filename=filename, user_id=fake_uuid, filedata=data)

    mocked_s3_upload.assert_called_once_with(
        filedata=data,
        region=bucket_credentials["region"],
        file_location=upload_filename,
        bucket_name=bucket_credentials["bucket"],
        content_type="image/png",
        access_key=bucket_credentials["access_key_id"],
        secret_key=bucket_credentials["secret_access_key"],
    )


def test_persist_logo(
    client_request, bucket_credentials, mocker, fake_uuid, upload_filename
):
    mocked_get_s3_object = mocker.patch("app.s3_client.s3_logo_client.get_s3_object")
    mocked_delete_s3_object = mocker.patch(
        "app.s3_client.s3_logo_client.delete_s3_object"
    )

    new_filename = permanent_email_logo_name(upload_filename, fake_uuid)

    persist_logo(upload_filename, new_filename)

    mocked_get_s3_object.assert_called_once_with(
        bucket_credentials["bucket"],
        new_filename,
        bucket_credentials["access_key_id"],
        bucket_credentials["secret_access_key"],
        bucket_credentials["region"],
    )
    mocked_delete_s3_object.assert_called_once_with(upload_filename)


def test_persist_logo_returns_if_not_temp(client_request, mocker, fake_uuid):
    filename = "logo.png"
    persist_logo(filename, filename)

    mocked_get_s3_object = mocker.patch("app.s3_client.s3_logo_client.get_s3_object")
    mocked_delete_s3_object = mocker.patch(
        "app.s3_client.s3_logo_client.delete_s3_object"
    )

    assert mocked_get_s3_object.called is False
    assert mocked_delete_s3_object.called is False


def test_permanent_email_logo_name_removes_TEMP_TAG_from_filename(
    upload_filename, fake_uuid
):
    new_name = permanent_email_logo_name(upload_filename, fake_uuid)

    assert new_name == "test_uuid-test.png"


def test_permanent_email_logo_name_does_not_change_filenames_with_no_TEMP_TAG():
    filename = "logo.png"
    new_name = permanent_email_logo_name(filename, filename)

    assert new_name == filename


def test_delete_email_temp_files_created_by_user(client_request, mocker, fake_uuid):
    obj = namedtuple("obj", ["key"])
    objs = [obj(key="test1"), obj(key="test2")]

    mocker.patch(
        "app.s3_client.s3_logo_client.get_s3_objects_filter_by_prefix",
        return_value=objs,
    )
    mocked_delete_s3_object = mocker.patch(
        "app.s3_client.s3_logo_client.delete_s3_object"
    )

    delete_email_temp_files_created_by(fake_uuid)

    for index, arg in enumerate(mocked_delete_s3_object.call_args_list):
        assert arg == call(objs[index].key)


def test_delete_single_email_temp_file(client_request, mocker, upload_filename):
    mocked_delete_s3_object = mocker.patch(
        "app.s3_client.s3_logo_client.delete_s3_object"
    )

    delete_email_temp_file(upload_filename)

    mocked_delete_s3_object.assert_called_with(upload_filename)


def test_does_not_delete_non_temp_email_file(client_request, mocker):
    filename = "logo.png"
    mocked_delete_s3_object = mocker.patch(
        "app.s3_client.s3_logo_client.delete_s3_object"
    )

    with pytest.raises(ValueError) as error:  # noqa: PT011  # Requires more research.
        delete_email_temp_file(filename)

    assert mocked_delete_s3_object.called is False
    assert str(error.value) == "Not a temp file: {}".format(filename)
