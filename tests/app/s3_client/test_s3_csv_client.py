from unittest.mock import Mock

from app.s3_client.s3_csv_client import remove_blank_lines, set_metadata_on_csv_upload


def test_sets_metadata(client_request, mocker):
    mocked_s3_object = Mock(
        bucket_name="test-csv-upload", key="service-1234-notify/5678.csv"
    )
    mocked_get_s3_object = mocker.patch(
        "app.s3_client.s3_csv_client.get_csv_upload",
        return_value=mocked_s3_object,
    )

    set_metadata_on_csv_upload("1234", "5678", foo="bar", baz=True)

    mocked_get_s3_object.assert_called_once_with("1234", "5678")
    mocked_s3_object.copy_from.assert_called_once_with(
        CopySource="test-csv-upload/service-1234-notify/5678.csv",
        Metadata={"baz": "True", "foo": "bar"},
        MetadataDirective="REPLACE",
        ServerSideEncryption="AES256",
    )


def test_removes_blank_lines():
    filedata = { "data": "variable,phone number\r\ntest,+15555555555\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n" }
    file_data = remove_blank_lines(filedata)
    assert file_data == {"data": "variable,phone number\r\ntest,+15555555555"}
