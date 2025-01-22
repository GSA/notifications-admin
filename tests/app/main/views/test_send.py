# -*- coding: utf-8 -*-
import uuid
from functools import partial
from glob import glob
from io import BytesIO
from itertools import repeat
from os import path
from random import randbytes
from unittest.mock import ANY
from uuid import uuid4
from zipfile import BadZipFile

import pytest
from flask import url_for
from notifications_python_client.errors import HTTPError
from xlrd.biffh import XLRDError
from xlrd.xldate import XLDateAmbiguous, XLDateError, XLDateNegative, XLDateTooLarge

from notifications_utils.recipients import RecipientCSV
from notifications_utils.template import SMSPreviewTemplate
from tests import (
    sample_uuid,
    validate_route_permission,
    validate_route_permission_with_client,
)
from tests.conftest import (
    SERVICE_ONE_ID,
    create_active_caseworking_user,
    create_active_user_with_permissions,
    create_multiple_email_reply_to_addresses,
    create_multiple_sms_senders,
    create_template,
    mock_get_service_email_template,
    mock_get_service_template,
    normalize_spaces,
)

FAKE_ONE_OFF_NOTIFICATION = {
    "links": {},
    "notifications": [
        {
            "api_key": None,
            "billable_units": 0,
            "carrier": None,
            "client_reference": None,
            "created_at": "2023-12-14T20:35:55+00:00",
            "created_by": {
                "email_address": "grsrbsrgsrf@fake.gov",
                "id": "de059e0a-42e5-48bb-939e-4f76804ab739",
                "name": "grsrbsrgsrf",
            },
            "document_download_count": None,
            "id": "a3442b43-0ba1-4854-9e0a-d2fba1cc9b81",
            "international": False,
            "job": {
                "id": "55b242b5-9f62-4271-aff7-039e9c320578",
                "original_file_name": "1127b78e-a4a8-4b70-8f4f-9f4fbf03ece2.csv",
            },
            "job_row_number": 0,
            "key_name": None,
            "key_type": "normal",
            "normalised_to": "+16615555555",
            "notification_type": "sms",
            "personalisation": {
                "dayofweek": "2",
                "favecolor": "3",
                "phonenumber": "+16615555555",
            },
            "phone_prefix": "1",
            "provider_response": None,
            "rate_multiplier": 1.0,
            "reference": None,
            "reply_to_text": "development",
            "sent_at": None,
            "sent_by": None,
            "service": "f62d840f-8bcb-4b36-b959-4687e16dd1a1",
            "status": "created",
            "template": {
                "content": "((day of week)) and ((fave color))",
                "id": "bd9caa7e-00ee-4c5a-839e-10ae1a7e6f73",
                "name": "personalized",
                "redact_personalisation": False,
                "subject": None,
                "template_type": "sms",
                "version": 1,
            },
            "to": "+16615555555",
            "updated_at": None,
        }
    ],
    "page_size": 50,
    "total": 1,
}

template_types = ["email", "sms"]

unchanging_fake_uuid = uuid.uuid4()

# The * ignores hidden files, eg .DS_Store
test_spreadsheet_files = glob(path.join("tests", "spreadsheet_files", "*"))
test_non_spreadsheet_files = glob(path.join("tests", "non_spreadsheet_files", "*"))


def test_show_correct_title_and_description_for_email_sender_type(
    client_request,
    fake_uuid,
    mock_get_service_email_template,
    multiple_reply_to_email_addresses,
):
    page = client_request.get(
        ".set_sender", service_id=SERVICE_ONE_ID, template_id=fake_uuid
    )

    assert (
        page.select_one(".usa-fieldset h1").text.strip()
        == "Where should replies come back to?"
    )


def test_show_correct_title_and_description_for_sms_sender_type(
    client_request,
    fake_uuid,
    mock_get_service_template,
    multiple_sms_senders,
):
    page = client_request.get(
        ".set_sender", service_id=SERVICE_ONE_ID, template_id=fake_uuid
    )

    assert (
        page.select_one(".usa-fieldset h1").text.strip()
        == "Who should the message come from?"
    )


def test_default_email_sender_is_checked_and_has_hint(
    client_request,
    fake_uuid,
    mock_get_service_email_template,
    multiple_reply_to_email_addresses,
):
    page = client_request.get(
        ".set_sender", service_id=SERVICE_ONE_ID, template_id=fake_uuid
    )

    assert page.select(".usa-radios input")[0].has_attr("checked")
    assert (
        normalize_spaces(page.select_one(".usa-radios .usa-hint").text) == "(Default)"
    )
    assert not page.select(".usa-radios input")[1].has_attr("checked")


def test_default_sms_sender_is_checked_and_has_hint(
    client_request,
    fake_uuid,
    mock_get_service_template,
    multiple_sms_senders_with_diff_default,
):
    page = client_request.get(
        ".set_sender", service_id=SERVICE_ONE_ID, template_id=fake_uuid
    )

    assert page.select(".usa-radios input")[0].has_attr("checked")
    assert (
        normalize_spaces(page.select_one(".usa-radios .usa-hint").text) == "(Default)"
    )
    assert not page.select(".usa-radios input")[1].has_attr("checked")


def test_default_sms_sender_is_checked_and_has_hint_when_there_are_no_inbound_numbers(
    client_request,
    fake_uuid,
    mock_get_service_template,
    multiple_sms_senders_no_inbound,
):
    page = client_request.get(
        ".set_sender", service_id=SERVICE_ONE_ID, template_id=fake_uuid
    )

    assert page.select(".usa-radios input")[0].has_attr("checked")
    assert (
        normalize_spaces(page.select_one(".usa-radios .usa-hint").text) == "(Default)"
    )
    assert not page.select(".usa-radios input")[1].has_attr("checked")


def test_default_inbound_sender_is_checked_and_has_hint_with_default_and_receives_text(
    client_request,
    service_one,
    fake_uuid,
    mock_get_service_template,
    multiple_sms_senders,
):
    page = client_request.get(
        ".set_sender", service_id=service_one["id"], template_id=fake_uuid
    )

    assert page.select(".usa-radios input")[0].has_attr("checked")
    assert (
        normalize_spaces(page.select_one(".usa-radios .usa-hint").text)
        == "(Default and receives replies)"
    )
    assert not page.select(".usa-radios input")[1].has_attr("checked")
    assert not page.select(".usa-radios input")[2].has_attr("checked")


def test_sms_sender_has_receives_replies_hint(
    client_request,
    service_one,
    fake_uuid,
    mock_get_service_template,
    multiple_sms_senders,
):
    page = client_request.get(
        ".set_sender", service_id=service_one["id"], template_id=fake_uuid
    )

    assert page.select(".usa-radios input")[0].has_attr("checked")
    assert (
        normalize_spaces(page.select_one(".usa-radios .usa-hint").text)
        == "(Default and receives replies)"
    )
    assert not page.select(".usa-radios input")[1].has_attr("checked")
    assert not page.select(".usa-radios input")[2].has_attr("checked")


@pytest.mark.parametrize(
    ("template_type", "sender_data"),
    [
        (
            "email",
            create_multiple_email_reply_to_addresses(),
        ),
        ("sms", create_multiple_sms_senders()),
    ],
)
def test_sender_session_is_present_after_selected(
    client_request, service_one, fake_uuid, template_type, sender_data, mocker
):
    template_data = create_template(template_type=template_type)
    mocker.patch(
        "app.service_api_client.get_service_template",
        return_value={"data": template_data},
    )

    if template_type == "email":
        mocker.patch(
            "app.service_api_client.get_reply_to_email_addresses",
            return_value=sender_data,
        )
    else:
        mocker.patch("app.service_api_client.get_sms_senders", return_value=sender_data)

    client_request.post(
        ".set_sender",
        service_id=service_one["id"],
        template_id=fake_uuid,
        _data={"sender": "1234"},
    )

    with client_request.session_transaction() as session:
        assert session["sender_id"] == "1234"


def test_set_sender_redirects_if_no_reply_to_email_addresses(
    client_request,
    fake_uuid,
    mock_get_service_email_template,
    no_reply_to_email_addresses,
):
    client_request.get(
        ".set_sender",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _expected_status=302,
        _expected_url=url_for(
            ".send_one_off",
            service_id=SERVICE_ONE_ID,
            template_id=fake_uuid,
        ),
    )


def test_set_sender_redirects_if_no_sms_senders(
    client_request,
    fake_uuid,
    mock_get_service_template,
    no_sms_senders,
):
    client_request.get(
        ".set_sender",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _expected_status=302,
        _expected_url=url_for(
            ".send_one_off",
            service_id=SERVICE_ONE_ID,
            template_id=fake_uuid,
        ),
    )


def test_set_sender_redirects_if_one_email_sender(
    client_request,
    fake_uuid,
    mock_get_service_email_template,
    single_reply_to_email_address,
):
    client_request.get(
        ".set_sender",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _expected_status=302,
        _expected_url=url_for(
            ".send_one_off",
            service_id=SERVICE_ONE_ID,
            template_id=fake_uuid,
        ),
    )

    with client_request.session_transaction() as session:
        assert session["sender_id"] == "1234"


def test_set_sender_redirects_if_one_sms_sender(
    client_request,
    fake_uuid,
    mock_get_service_template,
    single_sms_sender,
):
    client_request.get(
        ".set_sender",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _expected_status=302,
        _expected_url=url_for(
            ".send_one_off",
            service_id=SERVICE_ONE_ID,
            template_id=fake_uuid,
        ),
    )

    with client_request.session_transaction() as session:
        assert session["sender_id"] == "1234"


@pytest.mark.parametrize(
    ("sender_data"),
    [
        (create_multiple_sms_senders(isdefault1=True)),
    ],
)
def test_usnotify_and_notifygov_sms_sender_removal_not_default(sender_data, mocker):
    from app.main.views.send import remove_notify_from_sender_options

    sender_details = remove_notify_from_sender_options(sender_data)

    assert len(sender_details) == 2


@pytest.mark.parametrize(
    ("sender_data"),
    [
        (create_multiple_sms_senders(isdefault1=False, isdefault3=True)),
        (create_multiple_sms_senders(isdefault1=False, isdefault4=True)),
    ],
)
def test_usnotify_and_notifygov_sms_sender_removal_if_default(sender_data, mocker):
    from app.main.views.send import remove_notify_from_sender_options

    sender_details = remove_notify_from_sender_options(sender_data)

    assert len(sender_details) == 3


def test_that_test_files_exist():
    assert len(test_spreadsheet_files) == 8
    assert len(test_non_spreadsheet_files) == 6


def test_should_not_allow_files_to_be_uploaded_without_the_correct_permission(
    client_request,
    mock_get_service_template,
    service_one,
    fake_uuid,
):
    template_id = fake_uuid
    service_one["permissions"] = []

    page = client_request.get(
        ".send_messages",
        service_id=SERVICE_ONE_ID,
        template_id=template_id,
        _follow_redirects=True,
        _expected_status=403,
    )

    assert (
        page.select("main p")[0].text.strip()
        == "Sending text messages has been disabled for your service."
    )
    assert page.select(".usa-back-link")[0].text == "Back"
    assert page.select(".usa-back-link")[0]["href"] == url_for(
        ".view_template",
        service_id=service_one["id"],
        template_id=template_id,
    )


def test_example_spreadsheet(
    client_request,
    mock_get_service_template_with_placeholders_same_as_recipient,
    fake_uuid,
):
    page = client_request.get(
        ".send_messages", service_id=SERVICE_ONE_ID, template_id=fake_uuid
    )

    assert normalize_spaces(page.select_one("tbody tr").text) == (
        "1 phone number name date"
    )
    assert page.select_one("input[type=file]").has_attr("accept")
    assert (
        page.select_one("input[type=file]")["accept"]
        == ".csv,.xlsx,.xls,.ods,.xlsm,.tsv"
    )


@pytest.mark.parametrize(
    ("filename", "acceptable_file", "expected_status"),
    list(zip(test_spreadsheet_files, repeat(True), repeat(302)))
    + list(zip(test_non_spreadsheet_files, repeat(False), repeat(200))),
)
def test_upload_files_in_different_formats(
    filename,
    acceptable_file,
    expected_status,
    client_request,
    service_one,
    mocker,
    mock_get_service_template,
    fake_uuid,
):

    mock_s3_set_metadata = mocker.patch(
        "app.main.views.send.set_metadata_on_csv_upload"
    )

    mock_s3_upload = mocker.patch("app.main.views.send.s3upload")

    with open(filename, "rb") as uploaded:
        page = client_request.post(
            "main.send_messages",
            service_id=service_one["id"],
            template_id=fake_uuid,
            _data={"file": (BytesIO(uploaded.read()), filename)},
            _content_type="multipart/form-data",
            _expected_status=expected_status,
        )

    if acceptable_file:
        assert mock_s3_upload.call_args[0][1]["data"].strip() == (
            "phone number,name,favourite colour,fruit\r\n"
            "202 946 8050,Pete,Coral,tomato\r\n"
            "202 712 5974,Not Pete,Magenta,Avacado\r\n"
            "202 205 8823,Still Not Pete,Crimson,Pear"
        )
        mock_s3_set_metadata.assert_called_once_with(
            SERVICE_ONE_ID, ANY, original_file_name=filename
        )
    else:
        assert not mock_s3_upload.called
        assert normalize_spaces(page.select_one(".banner-dangerous").text) == (
            "Could not read {}. Try using a different file format.".format(filename)
        )


def test_send_messages_sanitises_and_truncates_file_name_for_metadata(
    client_request,
    service_one,
    mocker,
    mock_get_service_template_with_placeholders,
    mock_get_job_doesnt_exist,
    fake_uuid,
):

    mock_s3_set_metadata = mocker.patch(
        "app.main.views.send.set_metadata_on_csv_upload"
    )

    mocker.patch("app.main.views.send.s3upload")

    filename = f"😁{'a' * 2000}.csv"

    client_request.post(
        "main.send_messages",
        service_id=service_one["id"],
        template_id=fake_uuid,
        _data={"file": (BytesIO("".encode("utf-8")), filename)},
        _content_type="multipart/form-data",
        _follow_redirects=False,
    )

    assert len(mock_s3_set_metadata.call_args_list[0][1]["original_file_name"]) < len(
        filename
    )

    assert mock_s3_set_metadata.call_args_list[0][1]["original_file_name"].startswith(
        "?"
    )


@pytest.mark.parametrize(
    ("exception", "expected_error_message"),
    [
        (
            partial(UnicodeDecodeError, "codec", b"", 1, 2, "reason"),
            ("Could not read example.xlsx. Try using a different file format."),
        ),
        (
            BadZipFile,
            ("Could not read example.xlsx. Try using a different file format."),
        ),
        (
            XLRDError,
            ("Could not read example.xlsx. Try using a different file format."),
        ),
        (
            XLDateError,
            (
                "example.xlsx contains numbers or dates that Notify cannot understand. "
                "Try formatting all columns as ‘text’ or export your file as CSV."
            ),
        ),
        (
            XLDateNegative,
            (
                "example.xlsx contains numbers or dates that Notify cannot understand. "
                "Try formatting all columns as ‘text’ or export your file as CSV."
            ),
        ),
        (
            XLDateAmbiguous,
            (
                "example.xlsx contains numbers or dates that Notify cannot understand. "
                "Try formatting all columns as ‘text’ or export your file as CSV."
            ),
        ),
        (
            XLDateTooLarge,
            (
                "example.xlsx contains numbers or dates that Notify cannot understand. "
                "Try formatting all columns as ‘text’ or export your file as CSV."
            ),
        ),
    ],
)
def test_shows_error_if_parsing_exception(
    client_request,
    mocker,
    mock_get_service_template,
    exception,
    expected_error_message,
    fake_uuid,
):
    def _raise_exception_or_partial_exception(file_content, filename):
        raise exception()

    mocker.patch(
        "app.main.views.send.Spreadsheet.from_file",
        side_effect=_raise_exception_or_partial_exception,
    )

    page = client_request.post(
        "main.send_messages",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _data={"file": (BytesIO(b"example"), "example.xlsx")},
        _content_type="multipart/form-data",
        _expected_status=200,
    )

    assert normalize_spaces(page.select_one(".banner-dangerous").text) == (
        expected_error_message
    )


def test_upload_csv_file_with_errors_shows_check_page_with_errors(
    client_request,
    service_one,
    mocker,
    mock_get_service_template_with_placeholders,
    mock_get_users_by_service,
    mock_get_service_statistics,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
    fake_uuid,
):

    mocker.patch("app.main.views.send.set_metadata_on_csv_upload")

    mocker.patch(
        "app.main.views.send.get_csv_metadata",
        return_value={"original_file_name": "example.csv"},
    )
    mocker.patch("app.main.views.send.s3upload", return_value=sample_uuid())
    mocker.patch(
        "app.main.views.send.s3download",
        return_value="""
            phone number,name
            +12028675109
            +12028675109
        """,
    )

    page = client_request.post(
        "main.send_messages",
        service_id=service_one["id"],
        template_id=fake_uuid,
        _data={"file": (BytesIO("".encode("utf-8")), "example.csv")},
        _content_type="multipart/form-data",
        _follow_redirects=True,
    )

    with client_request.session_transaction() as session:
        assert "file_uploads" not in session

    assert page.select_one("input[type=file]").has_attr("accept")
    assert (
        page.select_one("input[type=file]")["accept"]
        == ".csv,.xlsx,.xls,.ods,.xlsm,.tsv"
    )

    assert "There’s a problem with example.csv" in page.text
    assert "+12028675109" in page.text
    assert "Missing" in page.text
    assert "Upload your file again" in page.text


def test_upload_csv_file_with_empty_message_shows_check_page_with_errors(
    client_request,
    service_one,
    mocker,
    mock_get_empty_service_template_with_optional_placeholder,
    mock_get_users_by_service,
    mock_get_service_statistics,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
    fake_uuid,
):

    mocker.patch("app.main.views.send.set_metadata_on_csv_upload")

    mocker.patch(
        "app.main.views.send.get_csv_metadata",
        return_value={"original_file_name": "example.csv"},
    )
    mocker.patch("app.main.views.send.s3upload", return_value=sample_uuid())

    mocker.patch(
        "app.main.views.send.s3download",
        return_value="""
            phone number, show_placeholder
            +12028675109, yes
            +12028675109, no
        """,
    )

    page = client_request.post(
        "main.send_messages",
        service_id=service_one["id"],
        template_id=fake_uuid,
        _data={"file": (BytesIO("".encode("utf-8")), "example.csv")},
        _content_type="multipart/form-data",
        _follow_redirects=True,
    )

    with client_request.session_transaction() as session:
        assert "file_uploads" not in session

    assert normalize_spaces(page.select_one(".banner-dangerous").text) == (
        "There’s a problem with example.csv "
        "You need to check you have content for the empty message in 1 row."
    )
    assert [normalize_spaces(row.text) for row in page.select("tbody tr")] == [
        "3 No content for this message",
        "+12028675109 no",
    ]
    assert normalize_spaces(page.select_one(".table-field-index").text) == "3"
    assert page.select_one(".table-field-index")["rowspan"] == "2"
    assert normalize_spaces(page.select("tbody tr td")[0].text) == "3"
    assert normalize_spaces(page.select("tbody tr td")[1].text) == (
        "No content for this message"
    )
    assert page.select("tbody tr td")[1]["colspan"] == "2"


def test_upload_csv_file_with_very_long_placeholder_shows_check_page_with_errors(
    client_request,
    service_one,
    mocker,
    mock_get_service_template_with_placeholders,
    mock_get_users_by_service,
    mock_get_service_statistics,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
    fake_uuid,
):

    mocker.patch("app.main.views.send.set_metadata_on_csv_upload")

    mocker.patch(
        "app.main.views.send.get_csv_metadata",
        return_value={"original_file_name": "example.csv"},
    )
    mocker.patch("app.main.views.send.s3upload", return_value=sample_uuid())
    big_placeholder = " ".join(["not ok"] * 402)
    mocker.patch(
        "app.main.views.send.s3download",
        return_value=f"""
            phone number, name
            +12028675109, {big_placeholder}
            +12027700900, {big_placeholder}
        """,
    )

    page = client_request.post(
        "main.send_messages",
        service_id=service_one["id"],
        template_id=fake_uuid,
        _data={"file": (BytesIO("".encode("utf-8")), "example.csv")},
        _content_type="multipart/form-data",
        _follow_redirects=True,
    )

    with client_request.session_transaction() as session:
        assert "file_uploads" not in session

    assert normalize_spaces(page.select_one(".banner-dangerous").text) == (
        "There’s a problem with example.csv "
        "You need to shorten the messages in 2 rows."
    )
    assert [normalize_spaces(row.text) for row in page.select("tbody tr")] == [
        "2 Message is too long",
        f"+12028675109 {big_placeholder}",
        "3 Message is too long",
        f"+12027700900 {big_placeholder}",
    ]
    assert normalize_spaces(page.select_one(".table-field-index").text) == "2"
    assert page.select_one(".table-field-index")["rowspan"] == "2"
    assert normalize_spaces(page.select("tbody tr td")[0].text) == "2"
    assert normalize_spaces(page.select("tbody tr td")[1].text) == (
        "Message is too long"
    )
    assert page.select("tbody tr td")[1]["colspan"] == "2"


@pytest.mark.parametrize(
    ("file_contents", "expected_error"),
    [
        (
            """
            telephone,name
            +12028675109
        """,
            (
                "There’s a problem with your column names "
                "Your file needs a column called ‘phone number’. "
                "Right now it has columns called ‘telephone’ and ‘name’."
            ),
        ),
        (
            """
            phone number
            +12028675109
        """,
            (
                "Your column names need to match the double brackets in your template "
                "Your file is missing a column called ‘name’."
            ),
        ),
        (
            """
            phone number, phone number, PHONE_NUMBER
            +12027900111,+12027900222,+12027900333,
        """,
            (
                "There’s a problem with your column names "
                "We found more than one column called ‘phone number’ or ‘PHONE_NUMBER’. "
                "Delete or rename one of these columns and try again."
            ),
        ),
        (
            """
            phone number, name
        """,
            ("Your file is missing some rows " "It needs at least one row of data."),
        ),
        (
            "+12028675109",
            (
                "Your file is missing some rows "
                "It needs at least one row of data, and columns called ‘name’ and ‘phone number’."
            ),
        ),
        (
            "",
            (
                "Your file is missing some rows "
                "It needs at least one row of data, and columns called ‘name’ and ‘phone number’."
            ),
        ),
        (
            """
            phone number, name
            +12028675109, example
            , example
            +12028675109, example
        """,
            (
                "There’s a problem with example.csv "
                "You need to enter missing data in 1 row."
            ),
        ),
        (
            """
            phone number, name
            +12028675109, example
            +12028675109,
            +12028675109, example
        """,
            (
                "There’s a problem with example.csv "
                "You need to enter missing data in 1 row."
            ),
        ),
    ],
)
def test_upload_csv_file_with_missing_columns_shows_error(
    client_request,
    mocker,
    mock_get_service_template_with_placeholders,
    mock_get_users_by_service,
    mock_get_service_statistics,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
    service_one,
    fake_uuid,
    file_contents,
    expected_error,
):

    mocker.patch("app.main.views.send.set_metadata_on_csv_upload")

    mocker.patch(
        "app.main.views.send.get_csv_metadata",
        return_value={"original_file_name": "example.csv"},
    )
    mocker.patch("app.main.views.send.s3upload", return_value=sample_uuid())

    mocker.patch("app.main.views.send.s3download", return_value=file_contents)

    page = client_request.post(
        "main.send_messages",
        service_id=service_one["id"],
        template_id=fake_uuid,
        _data={"file": (BytesIO("".encode("utf-8")), "example.csv")},
        _follow_redirects=True,
    )

    with client_request.session_transaction() as session:
        assert "file_uploads" not in session

    assert page.select_one("input[type=file]").has_attr("accept")
    assert (
        page.select_one("input[type=file]")["accept"]
        == ".csv,.xlsx,.xls,.ods,.xlsm,.tsv"
    )
    assert normalize_spaces(page.select(".banner-dangerous")[0].text) == expected_error


def test_upload_csv_invalid_extension(
    client_request,
    mock_login,
    service_one,
    mock_get_service_template,
    fake_uuid,
):
    page = client_request.post(
        "main.send_messages",
        service_id=service_one["id"],
        template_id=fake_uuid,
        _data={"file": (BytesIO("contents".encode("utf-8")), "invalid.txt")},
        _content_type="multipart/form-data",
        _follow_redirects=True,
    )

    assert "invalid.txt is not a spreadsheet that Notify can read" in page.text


def test_upload_csv_size_too_big(
    client_request,
    mock_login,
    service_one,
    mock_get_service_template,
    fake_uuid,
):
    page = client_request.post(
        "main.send_messages",
        service_id=service_one["id"],
        template_id=fake_uuid,
        _data={"file": (BytesIO(randbytes(11_000_000)), "invalid.csv")},
        _content_type="multipart/form-data",
        _follow_redirects=True,
    )

    assert "File must be smaller than 10Mb" in page.text


def test_upload_valid_csv_redirects_to_check_page(
    client_request,
    mock_get_service_template_with_placeholders,
    fake_uuid,
    mocker,
):

    mocker.patch("app.main.views.send.set_metadata_on_csv_upload")

    mocker.patch("app.main.views.send.s3upload", return_value=sample_uuid())
    client_request.post(
        "main.send_messages",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _data={"file": (BytesIO("".encode("utf-8")), "valid.csv")},
        _expected_status=302,
        _expected_redirect=url_for(
            "main.check_messages",
            service_id=SERVICE_ONE_ID,
            template_id=fake_uuid,
            upload_id=fake_uuid,
        ),
    )


@pytest.mark.parametrize(
    (
        "extra_args",
        "expected_link_in_first_row",
        "expected_message",
    ),
    [
        (
            {},
            None,
            "Test Service: A, Template <em>content</em> with & entity",
        ),
        (
            {"row_index": 2},
            None,
            "Test Service: A, Template <em>content</em> with & entity",
        ),
        (
            {"row_index": 4},
            True,
            "Test Service: C, Template <em>content</em> with & entity",
        ),
    ],
)
def test_upload_valid_csv_shows_preview_and_table(
    client_request,
    mocker,
    mock_get_live_service,
    mock_get_service_template_with_placeholders,
    mock_get_users_by_service,
    mock_get_service_statistics,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
    fake_uuid,
    extra_args,
    expected_link_in_first_row,
    expected_message,
):

    mocker.patch(
        "app.main.views.send.get_csv_metadata",
        return_value={"original_file_name": "example.csv"},
    )
    with client_request.session_transaction() as session:
        session["file_uploads"] = {fake_uuid: {"template_id": fake_uuid}}

    mocker.patch(
        "app.main.views.send.s3download",
        return_value="""
        phone number,name,thing,thing,thing
        2028675301, A,   foo,  foo,  foo
        2028675302, B,   foo,  foo,  foo
        2028675303, C,   foo,  foo,
    """,
    )

    page = client_request.post(
        "main.preview_job",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        upload_id=fake_uuid,
        **extra_args,
        _expected_status=200,
    )

    assert page.h1.text.strip() == "Preview"
    assert page.select("h2")[1].text.strip() == "Recipients list"
    assert page.h2.text.strip() == "Message"
    assert page.select_one(".sms-message-wrapper").text.strip() == expected_message
    assert not page.select_one(".table-field-index")

    for row_index, row in enumerate(
        [
            (
                '<td class="table-field-left-aligned"> <div> 2028675301 </div> </td>',
                '<td class="table-field-left-aligned"> <div> A </div> </td>',
                (
                    '<td class="table-field-left-aligned"> '
                    "<div> "
                    "<ul> "
                    "<li>foo</li> <li>foo</li> <li>foo</li> "
                    "</ul> "
                    "</div> "
                    "</td>"
                ),
            ),
            (
                '<td class="table-field-left-aligned"> <div> 2028675302 </div> </td>',
                '<td class="table-field-left-aligned"> <div> B </div> </td>',
                (
                    '<td class="table-field-left-aligned"> '
                    "<div> "
                    "<ul> "
                    "<li>foo</li> <li>foo</li> <li>foo</li> "
                    "</ul> "
                    "</div> "
                    "</td>"
                ),
            ),
            (
                '<td class="table-field-left-aligned"> <div> 2028675303 </div> </td>',
                '<td class="table-field-left-aligned"> <div> C </div> </td>',
                (
                    '<td class="table-field-left-aligned"> '
                    "<div> "
                    "<ul> "
                    "<li>foo</li> <li>foo</li> "
                    "</ul> "
                    "</div> "
                    "</td>"
                ),
            ),
        ]
    ):
        for index, cell in enumerate(row):
            row = page.select("table tbody tr")[row_index]
            assert "id" not in row
            assert normalize_spaces(str(row.select("td")[index])) == cell


def test_show_all_columns_if_there_are_duplicate_recipient_columns(
    client_request,
    mocker,
    mock_get_live_service,
    mock_get_service_template_with_placeholders,
    mock_get_users_by_service,
    mock_get_service_statistics,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
    fake_uuid,
):

    mocker.patch(
        "app.main.views.send.get_csv_metadata",
        return_value={"original_file_name": "example.csv"},
    )
    with client_request.session_transaction() as session:
        session["file_uploads"] = {fake_uuid: {"template_id": fake_uuid}}

    mocker.patch(
        "app.main.views.send.s3download",
        return_value="""
        phone number, phone_number, PHONENUMBER
        2028675301,  2028675302,  2028675303
    """,
    )

    page = client_request.get(
        "main.check_messages",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        upload_id=fake_uuid,
        _test_page_title=False,
    )

    assert normalize_spaces(page.select_one("thead").text) == (
        "Row in file1 phone number phone_number PHONENUMBER"
    )
    assert normalize_spaces(page.select_one("tbody").text) == (
        "2 2028675303 2028675303 2028675303"
    )


@pytest.mark.parametrize(
    ("row_index", "expected_status"),
    [
        (0, 404),
        (1, 404),
        (2, 200),
        (3, 200),
        (4, 200),
        (5, 404),
    ],
)
def test_404_for_previewing_a_row_out_of_range(
    client_request,
    mocker,
    mock_get_live_service,
    mock_get_service_template_with_placeholders,
    mock_get_users_by_service,
    mock_get_service_statistics,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
    fake_uuid,
    row_index,
    expected_status,
):

    mocker.patch("app.main.views.send.set_metadata_on_csv_upload")

    mocker.patch(
        "app.main.views.send.get_csv_metadata",
        return_value={"original_file_name": "example.csv"},
    )
    with client_request.session_transaction() as session:
        session["file_uploads"] = {fake_uuid: {"template_id": fake_uuid}}

    mocker.patch(
        "app.main.views.send.s3download",
        return_value="""
        phone number,name,thing,thing,thing
        2028675301, A,   foo,  foo,  foo
        2028675302, B,   foo,  foo,  foo
        2028675303, C,   foo,  foo,  foo
    """,
    )

    client_request.get(
        "main.check_messages",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        upload_id=fake_uuid,
        row_index=row_index,
        _expected_status=expected_status,
    )


@pytest.mark.parametrize("template_type", ["sms", "email"])
def test_send_one_off_step_redirects_to_start_if_session_not_setup(
    mocker,
    client_request,
    mock_get_service_statistics,
    mock_get_users_by_service,
    mock_has_no_jobs,
    fake_uuid,
    template_type,
):
    template_data = create_template(template_type=template_type, content="Hi ((name))")
    mocker.patch(
        "app.service_api_client.get_service_template",
        return_value={"data": template_data},
    )

    with client_request.session_transaction() as session:
        assert "recipient" not in session
        assert "placeholders" not in session

    client_request.get(
        "main.send_one_off_step",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        step_index=0,
        _expected_status=302,
        _expected_redirect=url_for(
            "main.send_one_off",
            service_id=SERVICE_ONE_ID,
            template_id=fake_uuid,
        ),
    )


def test_send_one_off_does_not_send_without_the_correct_permissions(
    client_request,
    mock_get_service_template,
    service_one,
    fake_uuid,
):
    template_id = fake_uuid
    service_one["permissions"] = []

    page = client_request.get(
        ".send_one_off",
        service_id=SERVICE_ONE_ID,
        template_id=template_id,
        _follow_redirects=True,
        _expected_status=403,
    )

    assert (
        page.select("main p")[0].text.strip()
        == "Sending text messages has been disabled for your service."
    )
    assert page.select(".usa-back-link")[0].text == "Back"
    assert page.select(".usa-back-link")[0]["href"] == url_for(
        ".view_template",
        service_id=service_one["id"],
        template_id=template_id,
    )


@pytest.mark.parametrize(
    "user",
    [
        create_active_user_with_permissions(),
        create_active_caseworking_user(),
    ],
)
def test_send_one_off_has_correct_page_title(
    client_request,
    service_one,
    mock_has_no_jobs,
    fake_uuid,
    mocker,
    user,
):
    client_request.login(user)
    template_data = create_template(
        template_type="sms", name="Two week reminder", content="Hi there ((name))"
    )
    mocker.patch(
        "app.service_api_client.get_service_template",
        return_value={"data": template_data},
    )

    page = client_request.get(
        "main.send_one_off",
        service_id=service_one["id"],
        template_id=fake_uuid,
        step_index=0,
        _follow_redirects=True,
    )
    assert page.h1.text.strip() == "Select recipients"

    assert len(page.select(".banner-tour")) == 0


@pytest.mark.parametrize(
    ("step_index", "prefilled", "expected_field_label"),
    [
        (
            0,
            {},
            "phone number",
        ),
        (
            1,
            {"phone number": "2020900123"},
            "one",
        ),
        (
            2,
            {"phone number": "2020900123", "one": "one"},
            "two",
        ),
    ],
)
def test_send_one_off_shows_placeholders_in_correct_order(
    client_request,
    fake_uuid,
    mock_has_no_jobs,
    mock_get_service_template_with_multiple_placeholders,
    step_index,
    prefilled,
    expected_field_label,
):
    with client_request.session_transaction() as session:
        session["recipient"] = None
        session["placeholders"] = prefilled

    page = client_request.get(
        "main.send_one_off_step",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        step_index=step_index,
    )

    assert normalize_spaces(page.select_one("label").text) == expected_field_label


@pytest.mark.parametrize(
    ("user", "template_type", "expected_link_text", "expected_link_url"),
    [
        (
            create_active_user_with_permissions(),
            "sms",
            "Use my phone number",
            partial(url_for, "main.send_one_off_to_myself"),
        ),
        (
            create_active_user_with_permissions(),
            "email",
            "Use my email address",
            partial(url_for, "main.send_one_off_to_myself"),
        ),
        (create_active_caseworking_user(), "sms", None, None),
    ],
)
def test_send_one_off_has_skip_link(
    client_request,
    service_one,
    fake_uuid,
    mock_get_service_email_template,
    mock_has_no_jobs,
    mocker,
    template_type,
    expected_link_text,
    expected_link_url,
    user,
):
    client_request.login(user)
    template_data = create_template(template_id=fake_uuid, template_type=template_type)
    mocker.patch(
        "app.service_api_client.get_service_template",
        return_value={"data": template_data},
    )

    page = client_request.get(
        "main.send_one_off_step",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        step_index=0,
        _follow_redirects=True,
    )

    skip_links = page.select("form a")

    if expected_link_text and expected_link_url:
        assert skip_links[1].text.strip() == expected_link_text
        assert skip_links[1]["href"] == expected_link_url(
            service_id=service_one["id"],
            template_id=fake_uuid,
        )
    else:
        with pytest.raises(IndexError):
            skip_links[1]


@pytest.mark.parametrize(
    ("template_type", "expected_sticky"),
    [
        ("sms", False),
        ("email", True),
    ],
)
def test_send_one_off_has_sticky_header_for_email(
    mocker,
    client_request,
    fake_uuid,
    mock_has_no_jobs,
    template_type,
    expected_sticky,
):
    template_data = create_template(template_type=template_type, content="((body))")
    mocker.patch(
        "app.service_api_client.get_service_template",
        return_value={"data": template_data},
    )

    page = client_request.get(
        "main.send_one_off_step",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        step_index=0,
        _follow_redirects=True,
    )

    assert bool(page.select(".js-stick-at-top-when-scrolling")) == expected_sticky


@pytest.mark.parametrize(
    "user",
    [
        create_active_user_with_permissions(),
        create_active_caseworking_user(),
    ],
)
def test_skip_link_will_not_show_on_sms_one_off_if_service_has_no_mobile_number(
    client_request,
    service_one,
    fake_uuid,
    mock_get_service_template,
    mock_has_no_jobs,
    mocker,
    user,
):
    user["mobile_number"] = None
    client_request.login(user)

    with client_request.session_transaction() as session:
        session["recipient"] = None
        session["placeholders"] = {}

    page = client_request.get(
        "main.send_one_off_step",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        step_index=0,
    )
    skip_link = page.findAll("a", text="Use my phone number")
    assert not skip_link


@pytest.mark.parametrize(
    "user",
    [
        create_active_user_with_permissions(),
        create_active_caseworking_user(),
    ],
)
def test_send_one_off_offers_link_to_upload(
    client_request,
    fake_uuid,
    mock_get_service_template,
    mock_has_jobs,
    user,
):
    client_request.login(user)

    page = client_request.get(
        "main.send_one_off",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _follow_redirects=True,
    )
    back_link = page.select_one(".usa-back-link")
    link = page.select_one("form a")

    assert back_link.text.strip() == "Back"

    assert link.text.strip() == "Upload a list of phone numbers"
    assert link["href"] == url_for(
        "main.send_messages",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
    )


def test_send_one_off_has_link_to_use_existing_list(
    client_request,
    mock_get_service_template,
    mock_has_jobs,
    fake_uuid,
):
    page = client_request.get(
        "main.send_one_off",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _follow_redirects=True,
    )

    assert [(link.text, link["href"]) for link in page.select("form a")] == [
        (
            "Upload a list of phone numbers",
            url_for(
                "main.send_messages",
                service_id=SERVICE_ONE_ID,
                template_id=fake_uuid,
            ),
        ),
        (
            "Use my phone number",
            url_for(
                "main.send_one_off_to_myself",
                service_id=SERVICE_ONE_ID,
                template_id=fake_uuid,
            ),
        ),
    ]


@pytest.mark.parametrize(
    "user",
    [
        create_active_user_with_permissions(),
        create_active_caseworking_user(),
    ],
)
def test_link_to_upload_not_offered_when_entering_personalisation(
    client_request,
    fake_uuid,
    mock_get_service_template_with_placeholders,
    mock_has_jobs,
    user,
):
    client_request.login(user)

    with client_request.session_transaction() as session:
        session["recipient"] = "2029009009"
        session["placeholders"] = {"phone number": "2029009009"}

    page = client_request.get(
        "main.send_one_off_step",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        step_index=1,
    )

    # We’re entering personalization
    assert page.select_one("input[type=text]")["name"] == "placeholder_value"
    assert page.select_one("label[for=phone-number]").text.strip() == "name"
    # No ‘Upload’ link shown
    assert len(page.select("main a")) == 0
    assert "Upload" not in page.select_one("main").text


@pytest.mark.parametrize(
    "user",
    [
        create_active_user_with_permissions(),
        create_active_caseworking_user(),
    ],
)
def test_send_one_off_redirects_to_end_if_step_out_of_bounds(
    client_request,
    mock_has_no_jobs,
    mock_get_service_template_with_placeholders,
    fake_uuid,
    mocker,
    user,
):
    client_request.login(user)

    with client_request.session_transaction() as session:
        session["recipient"] = "2020900123"
        session["placeholders"] = {"name": "foo", "phone number": "2020900123"}

    client_request.get(
        "main.send_one_off_step",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        step_index=999,
        _expected_status=302,
        _expected_redirect=url_for(
            "main.check_notification",
            service_id=SERVICE_ONE_ID,
            template_id=fake_uuid,
        ),
    )


@pytest.mark.parametrize(
    "user",
    [
        create_active_user_with_permissions(),
        create_active_caseworking_user(),
    ],
)
def test_send_one_off_redirects_to_start_if_you_skip_steps(
    client_request,
    service_one,
    fake_uuid,
    mock_get_users_by_service,
    mock_get_service_statistics,
    mock_has_no_jobs,
    mocker,
    user,
):
    with client_request.session_transaction() as session:
        session["placeholders"] = {"address_line_1": "foo"}

    client_request.login(user)
    client_request.get(
        "main.send_one_off_step",
        service_id=service_one["id"],
        template_id=fake_uuid,
        step_index=7,
        _expected_redirect=url_for(
            "main.send_one_off",
            service_id=service_one["id"],
            template_id=fake_uuid,
        ),
    )


@pytest.mark.parametrize(
    "user",
    [
        create_active_user_with_permissions(),
        create_active_caseworking_user(),
    ],
)
def test_send_one_off_redirects_to_start_if_index_out_of_bounds_and_some_placeholders_empty(
    client_request,
    service_one,
    fake_uuid,
    mock_get_service_email_template,
    mock_get_users_by_service,
    mock_get_service_statistics,
    mock_has_no_jobs,
    mocker,
    user,
):
    client_request.login(user)
    with client_request.session_transaction() as session:
        session["placeholders"] = {"name": "foo"}

    client_request.get(
        "main.send_one_off_step",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        step_index=999,
        _expected_status=302,
        _expected_redirect=url_for(
            "main.send_one_off",
            service_id=SERVICE_ONE_ID,
            template_id=fake_uuid,
        ),
    )


@pytest.mark.parametrize(
    "user",
    [
        create_active_user_with_permissions(),
        create_active_caseworking_user(),
    ],
)
def test_send_one_off_sms_message_redirects(
    client_request,
    mocker,
    service_one,
    fake_uuid,
    user,
):
    client_request.login(user)
    template = {"data": {"template_type": "sms", "folder": None}}
    mocker.patch("app.service_api_client.get_service_template", return_value=template)

    client_request.get(
        "main.send_one_off",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _expected_status=302,
        _expected_response=url_for(
            "main.send_one_off_step",
            service_id=SERVICE_ONE_ID,
            template_id=fake_uuid,
            step_index=0,
        ),
    )


@pytest.mark.parametrize(
    "user",
    [
        create_active_user_with_permissions(),
        create_active_caseworking_user(),
    ],
)
def test_send_one_off_email_to_self_without_placeholders_redirects_to_check_page(
    client_request,
    mocker,
    service_one,
    mock_get_service_email_template_without_placeholders,
    mock_get_users_by_service,
    mock_get_service_statistics,
    mock_has_no_jobs,
    fake_uuid,
    user,
):
    client_request.login(user)

    with client_request.session_transaction() as session:
        session["recipient"] = "foo@bar.com"
        session["placeholders"] = {"email address": "foo@bar.com"}

    page = client_request.get(
        "main.send_one_off_step",
        step_index=1,
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _follow_redirects=True,
    )

    assert page.select("h1")[0].text.strip() == "Select delivery time"


@pytest.mark.parametrize(
    ("permissions", "expected_back_link_endpoint", "extra_args"),
    [
        (
            {"send_messages", "manage_templates"},
            "main.view_template",
            {"template_id": unchanging_fake_uuid},
        ),
        (
            {"send_messages"},
            "main.choose_template",
            {},
        ),
        (
            {"send_messages", "view_activity"},
            "main.choose_template",
            {},
        ),
    ],
)
def test_send_one_off_step_0_back_link(
    client_request,
    active_user_with_permissions,
    mock_login,
    mock_get_service,
    mock_get_service_template_with_placeholders,
    mock_has_no_jobs,
    permissions,
    expected_back_link_endpoint,
    extra_args,
):
    active_user_with_permissions["permissions"][SERVICE_ONE_ID] = permissions
    client_request.login(active_user_with_permissions)

    with client_request.session_transaction() as session:
        session["placeholders"] = {}
        session["recipient"] = None

    page = client_request.get(
        "main.send_one_off_step",
        service_id=SERVICE_ONE_ID,
        template_id=unchanging_fake_uuid,
        step_index=0,
    )

    assert page.select(".usa-back-link")[0]["href"] == url_for(
        expected_back_link_endpoint, service_id=SERVICE_ONE_ID, **extra_args
    )


def test_send_one_off_sms_message_back_link_with_multiple_placeholders(
    client_request,
    mock_get_service_template_with_multiple_placeholders,
    mock_has_no_jobs,
):
    with client_request.session_transaction() as session:
        session["recipient"] = "2020900123"
        session["placeholders"] = {"phone number": "2020900123", "one": "bar"}

    page = client_request.get(
        "main.send_one_off_step",
        service_id=SERVICE_ONE_ID,
        template_id=unchanging_fake_uuid,
        step_index=2,
    )

    assert page.select_one(".usa-back-link")["href"] == url_for(
        "main.send_one_off_step",
        service_id=SERVICE_ONE_ID,
        template_id=unchanging_fake_uuid,
        step_index=1,
    )


def test_send_one_off_populates_field_from_session(
    client_request,
    mocker,
    service_one,
    mock_login,
    mock_get_service,
    mock_get_service_template_with_placeholders,
    fake_uuid,
):
    with client_request.session_transaction() as session:
        session["recipient"] = None
        session["placeholders"] = {}
        session["placeholders"]["name"] = "Jo"

    page = client_request.get(
        "main.send_one_off_step",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        step_index=1,
    )

    assert page.select("input")[0]["value"] == "Jo"


def test_send_one_off_sms_message_puts_submitted_data_in_session(
    client_request,
    service_one,
    mock_get_service_template_with_placeholders,
    mock_get_users_by_service,
    mock_get_service_statistics,
    fake_uuid,
):
    with client_request.session_transaction() as session:
        session["recipient"] = "202-867-5303"
        session["placeholders"] = {"phone number": "202-867-5303"}

    client_request.post(
        "main.send_one_off_step",
        service_id=service_one["id"],
        template_id=fake_uuid,
        step_index=1,
        _data={"placeholder_value": "Jo"},
        _expected_status=302,
        _expected_redirect=url_for(
            "main.check_notification",
            service_id=service_one["id"],
            template_id=fake_uuid,
        ),
    )

    with client_request.session_transaction() as session:
        assert session["recipient"] == "202-867-5303"
        assert session["placeholders"] == {"phone number": "202-867-5303", "name": "Jo"}


def test_send_one_off_clears_session(
    client_request,
    mocker,
    service_one,
    fake_uuid,
):
    template = {"data": {"template_type": "sms", "folder": None}}
    mocker.patch("app.service_api_client.get_service_template", return_value=template)

    with client_request.session_transaction() as session:
        session["recipient"] = "2028675301"
        session["placeholders"] = {"foo": "bar"}

    client_request.get(
        "main.send_one_off",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _expected_status=302,
    )

    with client_request.session_transaction() as session:
        assert session["recipient"] is None
        assert session["placeholders"] == {}


def test_download_example_csv(
    client_request,
    mocker,
    api_user_active,
    mock_login,
    mock_get_service,
    mock_get_service_template_with_placeholders_same_as_recipient,
    mock_has_permissions,
    fake_uuid,
):
    response = client_request.get_response(
        "main.get_example_csv",
        service_id=fake_uuid,
        template_id=fake_uuid,
        follow_redirects=True,
    )
    assert response.get_data(as_text=True) == (
        "phone number,name,date\r\n" "12223334444,example,example\r\n"
    )
    assert "text/csv" in response.headers["Content-Type"]


def test_upload_csvfile_with_valid_phone_shows_all_numbers(
    client_request,
    mock_get_service_template,
    mock_get_users_by_service,
    mock_get_live_service,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
    service_one,
    fake_uuid,
    mocker,
):

    mock_s3_set_metadata = mocker.patch(
        "app.main.views.send.set_metadata_on_csv_upload"
    )

    mocker.patch(
        "app.main.views.send.get_csv_metadata",
        return_value={"original_file_name": "example.csv"},
    )
    mocker.patch("app.main.views.send.s3upload", return_value=sample_uuid())
    mocker.patch(
        "app.main.views.send.s3download",
        return_value="\n".join(
            ["phone number"]
            + ["202 867 07{0:02d}".format(final_two) for final_two in range(0, 53)]
        ),
    )
    mock_get_notification_count = mocker.patch(
        "app.service_api_client.get_notification_count", return_value=0
    )
    page = client_request.post(
        "main.send_messages",
        service_id=service_one["id"],
        template_id=fake_uuid,
        _data={"file": (BytesIO("".encode("utf-8")), "example.csv")},
        _content_type="multipart/form-data",
        _follow_redirects=True,
    )
    with client_request.session_transaction() as session:
        assert "file_uploads" not in session

    assert mock_s3_set_metadata.call_count == 2
    assert mock_s3_set_metadata.call_args_list[0] == mocker.call(
        SERVICE_ONE_ID, fake_uuid, original_file_name="example.csv"
    )
    assert mock_s3_set_metadata.call_args_list[1] == mocker.call(
        SERVICE_ONE_ID,
        fake_uuid,
        notification_count=53,
        template_id=fake_uuid,
        valid=True,
        original_file_name="example.csv",
    )

    assert "Select delivery time" in page.text
    assert "202 867 0749" not in page.text
    assert "202 867 0750" not in page.text

    mock_get_notification_count.assert_called_with(service_one["id"])


@pytest.mark.parametrize(
    ("international_sms_permission", "should_allow_international"),
    [
        (False, False),
        (True, True),
    ],
)
def test_upload_csvfile_with_international_validates(
    mocker,
    api_user_active,
    client_request,
    mock_get_service_template,
    mock_has_permissions,
    mock_get_users_by_service,
    mock_get_service_statistics,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
    fake_uuid,
    international_sms_permission,
    should_allow_international,
    service_one,
):

    mocker.patch("app.main.views.send.set_metadata_on_csv_upload")

    mocker.patch(
        "app.main.views.send.get_csv_metadata",
        return_value={"original_file_name": "example.csv"},
    )
    mocker.patch("app.main.views.send.s3upload", return_value=sample_uuid())
    if international_sms_permission:
        service_one["permissions"] += ("sms", "international_sms")
    mocker.patch(
        "app.service_api_client.get_service", return_value={"data": service_one}
    )

    mocker.patch("app.main.views.send.s3download", return_value="")
    mock_recipients = mocker.patch(
        "app.main.views.send.RecipientCSV",
        return_value=RecipientCSV(
            "", template=SMSPreviewTemplate({"content": "foo", "template_type": "sms"})
        ),
    )

    client_request.post(
        "main.send_messages",
        service_id=fake_uuid,
        template_id=fake_uuid,
        _data={"file": (BytesIO("".encode("utf-8")), "example.csv")},
        _content_type="multipart/form-data",
        _follow_redirects=True,
    )

    assert (
        mock_recipients.call_args[1]["allow_international_sms"]
        == should_allow_international
    )


def test_test_message_can_only_be_sent_now(
    client_request,
    mocker,
    service_one,
    mock_get_service_template,
    mock_get_users_by_service,
    mock_get_service_statistics,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
    mock_s3_download,
    fake_uuid,
):

    mocker.patch("app.main.views.send.set_metadata_on_csv_upload")

    mocker.patch(
        "app.main.views.send.get_csv_metadata",
        return_value={"original_file_name": "example.csv"},
    )
    content = client_request.get(
        "main.check_messages",
        service_id=service_one["id"],
        upload_id=fake_uuid,
        template_id=fake_uuid,
        from_test=True,
    )

    assert 'name="scheduled_for"' not in content


def test_preview_button_is_correctly_labelled(
    client_request,
    mocker,
    mock_get_live_service,
    mock_get_service_template,
    mock_get_users_by_service,
    mock_get_service_statistics,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
    fake_uuid,
):

    mocker.patch(
        "app.main.views.send.get_csv_metadata",
        return_value={"original_file_name": "example.csv"},
    )
    mocker.patch(
        "app.main.views.send.s3download",
        return_value="\n".join(["phone_number"] + (["2028670123"] * 1000)),
    )
    mocker.patch("app.main.views.send.set_metadata_on_csv_upload")

    page = client_request.get(
        "main.check_messages",
        service_id=SERVICE_ONE_ID,
        upload_id=fake_uuid,
        template_id=fake_uuid,
    )

    assert normalize_spaces(page.select_one("main [type=submit]").text) == ("Preview")


@pytest.mark.parametrize("when", ["", "2016-08-25T13:04:21.767198"])
def test_create_job_should_call_api(
    client_request,
    mock_create_job,
    mock_get_job,
    mock_get_notifications,
    mock_get_service_template,
    mock_get_service_data_retention,
    mocker,
    fake_uuid,
    when,
):
    data = mock_get_job(SERVICE_ONE_ID, fake_uuid)["data"]
    job_id = data["id"]
    original_file_name = data["original_file_name"]
    template_id = data["template"]
    notification_count = data["notification_count"]
    with client_request.session_transaction() as session:
        session["file_uploads"] = {
            fake_uuid: {
                "template_id": template_id,
                "notification_count": notification_count,
                "valid": True,
            }
        }
    with client_request.session_transaction() as session:
        session["scheduled_for"] = when

    page = client_request.post(
        "main.start_job",
        service_id=SERVICE_ONE_ID,
        upload_id=job_id,
        original_file_name=original_file_name,
        _data={
            "scheduled_for": when,
        },
        _follow_redirects=True,
        _expected_status=200,
    )

    assert "Message status" in page.text

    mock_create_job.assert_called_with(
        job_id,
        SERVICE_ONE_ID,
        scheduled_for=when,
    )


@pytest.mark.parametrize(
    ("route", "response_code"),
    [
        ("main.send_messages", 200),
        ("main.get_example_csv", 200),
        ("main.send_one_off", 302),
    ],
)
def test_route_permissions(
    mocker,
    notify_admin,
    client_request,
    api_user_active,
    service_one,
    mock_get_service_template,
    mock_get_service_templates,
    mock_get_jobs,
    mock_get_notifications,
    mock_create_job,
    fake_uuid,
    route,
    response_code,
):
    validate_route_permission(
        mocker,
        notify_admin,
        "GET",
        response_code,
        url_for(route, service_id=service_one["id"], template_id=fake_uuid),
        ["view_activity", "send_messages"],
        api_user_active,
        service_one,
    )


@pytest.mark.parametrize(
    ("route", "response_code", "method"),
    [("main.check_notification", 200, "GET"), ("main.send_notification", 302, "POST")],
)
def test_route_permissions_send_check_notifications(
    mocker,
    notify_admin,
    client_request,
    api_user_active,
    service_one,
    mock_send_notification,
    mock_get_service_template,
    fake_uuid,
    route,
    response_code,
    method,
    mock_create_job,
):
    mocker.patch("app.main.views.send.s3upload", return_value=sample_uuid())
    with client_request.session_transaction() as session:
        session["recipient"] = "2028675301"
        session["placeholders"] = {"name": "a"}

    mocker.patch("app.main.views.send.check_messages")
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )

    validate_route_permission_with_client(
        mocker,
        client_request,
        method,
        response_code,
        url_for(route, service_id=service_one["id"], template_id=fake_uuid),
        ["send_messages"],
        api_user_active,
        service_one,
    )


@pytest.mark.parametrize(
    ("route", "expected_status"),
    [
        ("main.send_messages", 403),
        ("main.get_example_csv", 403),
        ("main.send_one_off", 403),
    ],
)
def test_route_permissions_sending(
    mocker,
    notify_admin,
    client_request,
    api_user_active,
    service_one,
    mock_get_service_template,
    mock_get_service_templates,
    mock_get_jobs,
    mock_get_notifications,
    mock_create_job,
    fake_uuid,
    route,
    expected_status,
):
    validate_route_permission(
        mocker,
        notify_admin,
        "GET",
        expected_status,
        url_for(
            route,
            service_id=service_one["id"],
            template_type="sms",
            template_id=fake_uuid,
        ),
        ["blah"],
        api_user_active,
        service_one,
    )


@pytest.mark.parametrize(
    ("template_type", "has_placeholders", "extra_args", "expected_url"),
    [
        ("sms", False, dict(), partial(url_for, ".send_messages")),
        ("sms", True, dict(), partial(url_for, ".send_messages")),
        ("sms", True, dict(from_test=True), partial(url_for, ".send_one_off")),
    ],
)
def test_check_messages_back_link(
    client_request,
    mock_get_user_by_email,
    mock_get_users_by_service,
    mock_has_permissions,
    mock_get_service_statistics,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
    mock_s3_download,
    fake_uuid,
    mocker,
    template_type,
    has_placeholders,
    extra_args,
    expected_url,
):

    mocker.patch("app.main.views.send.set_metadata_on_csv_upload")

    mocker.patch(
        "app.main.views.send.get_csv_metadata",
        return_value={"original_file_name": "example.csv"},
    )
    content = "Hi there ((name))" if has_placeholders else "Hi there"
    template_data = create_template(
        template_id=fake_uuid, template_type=template_type, content=content
    )
    mocker.patch(
        "app.service_api_client.get_service_template",
        return_value={"data": template_data},
    )

    with client_request.session_transaction() as session:
        session["file_uploads"] = {
            fake_uuid: {
                "original_file_name": "valid.csv",
                "template_id": fake_uuid,
                "notification_count": 1,
                "valid": True,
            }
        }

    page = client_request.get(
        "main.check_messages",
        service_id=SERVICE_ONE_ID,
        upload_id=fake_uuid,
        template_id=fake_uuid,
        _test_page_title=False,
        **extra_args,
    )

    assert (page.find_all("a", {"class": "usa-back-link"})[0]["href"]) == expected_url(
        service_id=SERVICE_ONE_ID, template_id=fake_uuid
    )


@pytest.mark.parametrize(
    ("num_requested", "expected_msg"),
    [
        (None, "‘example.csv’ contains 1,234 phone numbers."),
        ("0", "‘example.csv’ contains 1,234 phone numbers."),
        # This used to trigger the too many messages errors but we removed the daily limit
        ("1", "‘example.csv’ contains 1,234 phone numbers."),
    ],
    ids=["none_sent", "none_sent", "some_sent"],
)
def test_check_messages_shows_too_many_messages_errors(
    mocker,
    client_request,
    mock_get_service,  # set message_limit to 50
    mock_get_users_by_service,
    mock_get_service_template,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
    fake_uuid,
    num_requested,
    expected_msg,
):

    mocker.patch(
        "app.main.views.send.get_csv_metadata",
        return_value={"original_file_name": "example.csv"},
    )
    # csv with 100 phone numbers
    mocker.patch(
        "app.main.views.send.s3download",
        return_value=",\n".join(
            ["phone number"]
            + ([mock_get_users_by_service(None)[0]["mobile_number"]] * 1234)
        ),
    )
    mocker.patch("app.extensions.redis_client.get", return_value=num_requested)

    with client_request.session_transaction() as session:
        session["file_uploads"] = {
            fake_uuid: {
                "template_id": fake_uuid,
                "notification_count": 1,
                "valid": True,
            }
        }

    page = client_request.get(
        "main.check_messages",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        upload_id=fake_uuid,
        _test_page_title=False,
    )

    assert page.find("h1").text.strip() == "Too many recipients"
    assert (
        page.find("div", class_="banner-dangerous").find("a").text.strip()
        == "trial mode"
    )

    # remove excess whitespace from element
    details = page.find("div", class_="banner-dangerous").find_all("p")[1]
    details = " ".join(
        [line.strip() for line in details.text.split("\n") if line.strip() != ""]
    )
    assert details == expected_msg


def test_check_messages_shows_trial_mode_error(
    client_request,
    mock_get_users_by_service,
    mock_get_service_template,
    mock_has_permissions,
    mock_get_service_statistics,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
    fake_uuid,
    mocker,
):

    mocker.patch(
        "app.main.views.send.get_csv_metadata",
        return_value={"original_file_name": "example.csv"},
    )
    mocker.patch(
        "app.main.views.send.s3download",
        return_value=("phone number,\n2028675209"),  # Not in team
    )

    with client_request.session_transaction() as session:
        session["file_uploads"] = {
            fake_uuid: {
                "template_id": "",
            }
        }

    page = client_request.get(
        "main.check_messages",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        upload_id=fake_uuid,
        _test_page_title=False,
    )

    assert " ".join(page.find("div", class_="banner-dangerous").text.split()) == (
        "You cannot send to this phone number "
        "In trial mode you can only send to yourself and members of your team"
    )


@pytest.mark.parametrize(
    "uploaded_file_name",
    [
        pytest.param("applicants.ods"),  # normal job
        pytest.param("send_me_later.csv"),  # should look at scheduled job
    ],
)
def test_warns_if_file_sent_already(
    client_request,
    mock_get_users_by_service,
    mock_get_live_service,
    mock_get_service_template,
    mock_has_permissions,
    mock_get_service_statistics,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
    fake_uuid,
    mocker,
    uploaded_file_name,
):
    mocker.patch(
        "app.main.views.send.s3download", return_value=("phone number,\n2028675209")
    )
    mocker.patch(
        "app.main.views.send.get_csv_metadata",
        return_value={"original_file_name": uploaded_file_name},
    )
    page = client_request.get(
        "main.check_messages",
        service_id=SERVICE_ONE_ID,
        template_id="5d729fbd-239c-44ab-b498-75a985f3198f",
        upload_id=fake_uuid,
        original_file_name=uploaded_file_name,
        _test_page_title=False,
    )

    assert normalize_spaces(page.select_one(".banner-dangerous").text) == (
        "These messages have already been sent today "
        "If you need to resend them, rename the file and upload it again."
    )

    mock_get_jobs.assert_called_once_with(SERVICE_ONE_ID, limit_days=0)


@pytest.mark.skip(reason="Test fails for unknown reason at this time.")
@pytest.mark.parametrize(
    "uploaded_file_name",
    [
        pytest.param("thisisatest.csv"),  # different template version
        pytest.param("full_of_regret.csv"),  # job is cancelled
    ],
)
def test_warns_if_file_sent_already_errors(
    client_request,
    mock_get_users_by_service,
    mock_get_live_service,
    mock_get_service_template,
    mock_has_permissions,
    mock_get_service_statistics,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
    fake_uuid,
    mocker,
    uploaded_file_name,
):
    mocker.patch(
        "app.main.views.send.s3download", return_value=("phone number,\n2028675209")
    )
    mocker.patch(
        "app.main.views.send.get_csv_metadata",
        return_value={"original_file_name": uploaded_file_name},
    )

    with pytest.raises(
        expected_exception=Exception, match="Unable to locate credentials"
    ):
        stmt_for_test_warns_if_file_sent_already_errors(
            client_request, uploaded_file_name, fake_uuid, mock_get_jobs
        )


def stmt_for_test_warns_if_file_sent_already_errors(
    client_request, uploaded_file_name, fake_uuid, mock_get_jobs
):
    page = client_request.get(
        "main.check_messages",
        service_id=SERVICE_ONE_ID,
        template_id="5d729fbd-239c-44ab-b498-75a985f3198f",
        upload_id=fake_uuid,
        original_file_name=uploaded_file_name,
        _test_page_title=False,
    )
    assert normalize_spaces(page.select_one(".banner-dangerous").text) == (
        "These messages have already been sent today "
        "If you need to resend them, rename the file and upload it again."
    )
    mock_get_jobs.assert_called_once_with(SERVICE_ONE_ID, limit_days=0)


def test_check_messages_column_error_doesnt_show_optional_columns(
    mocker,
    client_request,
    mock_get_service_template,
    mock_has_permissions,
    fake_uuid,
    mock_get_users_by_service,
    mock_get_service_statistics,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
):

    mocker.patch(
        "app.main.views.send.get_csv_metadata",
        return_value={"original_file_name": "example.csv"},
    )
    mocker.patch(
        "app.main.views.send.s3download",
        return_value="\n".join(
            ["address_line_1,address_line_2,foo"]
            + ["First Lastname,1 Example Road,SW1 1AA"]
        ),
    )

    with client_request.session_transaction() as session:
        session["file_uploads"] = {
            fake_uuid: {
                "template_id": "",
                "original_file_name": "",
            }
        }

    page = client_request.get(
        "main.check_messages",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        upload_id=fake_uuid,
        _test_page_title=False,
    )

    assert normalize_spaces(page.select_one(".banner-dangerous").text) == (
        "There’s a problem with your column names "
        "Your file needs a column called ‘phone number’. "
        "Right now it has columns called ‘address_line_1’, ‘address_line_2’ and ‘foo’."
    )


def test_check_messages_adds_sender_id_in_session_to_metadata(
    client_request,
    mocker,
    mock_get_live_service,
    mock_get_service_template,
    mock_get_users_by_service,
    mock_get_service_statistics,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
    fake_uuid,
):

    mock_s3_set_metadata = mocker.patch(
        "app.main.views.send.set_metadata_on_csv_upload"
    )

    mocker.patch(
        "app.main.views.send.get_csv_metadata",
        return_value={"original_file_name": "example.csv"},
    )
    mocker.patch(
        "app.main.views.send.s3download", return_value=("phone number,\n2028675209")
    )
    mocker.patch("app.main.views.send.get_sms_sender_from_session")

    with client_request.session_transaction() as session:
        session["file_uploads"] = {fake_uuid: {"template_id": fake_uuid}}
        session["sender_id"] = "fake-sender"

    client_request.get(
        "main.check_messages",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        upload_id=fake_uuid,
        _test_page_title=False,
    )

    mock_s3_set_metadata.assert_called_once_with(
        SERVICE_ONE_ID,
        fake_uuid,
        notification_count=1,
        template_id=fake_uuid,
        sender_id="fake-sender",
        valid=True,
        original_file_name="example.csv",
    )


def test_check_messages_shows_over_max_row_error(
    client_request,
    mock_get_users_by_service,
    mock_get_service_template_with_placeholders,
    mock_has_permissions,
    mock_get_service_statistics,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
    mock_s3_download,
    fake_uuid,
    mocker,
):

    mocker.patch(
        "app.main.views.send.get_csv_metadata",
        return_value={"original_file_name": "example.csv"},
    )
    mock_recipients = mocker.patch("app.main.views.send.RecipientCSV").return_value
    mock_recipients.max_rows = 11111
    mock_recipients.__len__.return_value = 99999
    mock_recipients.too_many_rows.return_value = True

    with client_request.session_transaction() as session:
        session["file_uploads"] = {
            fake_uuid: {
                "template_id": fake_uuid,
            }
        }

    page = client_request.get(
        "main.check_messages",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        upload_id=fake_uuid,
        _test_page_title=False,
    )

    assert " ".join(page.find("div", class_="banner-dangerous").text.split()) == (
        "Your file has too many rows "
        "Notify can process up to 11,111 rows at once. "
        "Your file has 99,999 rows."
    )


@pytest.mark.parametrize(
    "existing_session_items", [{}, {"recipient": "2028675301"}, {"name": "Jo"}]
)
def test_check_notification_redirects_if_session_not_populated(
    client_request,
    service_one,
    fake_uuid,
    existing_session_items,
    mock_get_service_template_with_placeholders,
):
    with client_request.session_transaction() as session:
        session.update(existing_session_items)

    client_request.get(
        "main.check_notification",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _expected_status=301,
        _expected_redirect=url_for(
            "main.send_one_off_step",
            service_id=SERVICE_ONE_ID,
            template_id=fake_uuid,
            step_index=1,
        ),
    )


def test_check_notification_shows_scheduler(
    client_request, service_one, fake_uuid, mock_get_service_template
):
    with client_request.session_transaction() as session:
        session["recipient"] = "2028675301"
        session["placeholders"] = {}

    page = client_request.get(
        "main.check_notification", service_id=service_one["id"], template_id=fake_uuid
    )

    assert page.h1.text.strip() == "Select delivery time"
    assert (page.find_all("a", {"class": "usa-back-link"})[0]["href"]) == url_for(
        "main.send_one_off_step",
        service_id=service_one["id"],
        template_id=fake_uuid,
        step_index=0,
    )

    # assert tour not visible
    assert not page.select(".banner-tour")

    # post to send_notification with help=0 to ensure no back link is then shown
    assert page.form.attrs["action"] == url_for(
        "main.preview_notification",
        service_id=service_one["id"],
        template_id=fake_uuid,
    )

    assert normalize_spaces(page.select_one("main [type=submit]").text) == ("Preview")


@pytest.mark.parametrize("when", ["", "2016-08-25T13:04:21.767198"])
def test_preview_notification_shows_preview(
    client_request,
    service_one,
    fake_uuid,
    mock_get_service_template,
    when,
):
    with client_request.session_transaction() as session:
        session["recipient"] = "15555555555"
        session["placeholders"] = {}

    page = client_request.post(
        "main.preview_notification",
        service_id=service_one["id"],
        template_id=fake_uuid,
        _expected_status=200,
    )
    assert page.h1.text.strip() == "Preview for sending"
    assert (page.find_all("a", {"class": "usa-back-link"})[0]["href"]) == url_for(
        "main.check_notification",
        service_id=service_one["id"],
        template_id=fake_uuid,
    )
    # assert tour not visible
    assert not page.select(".banner-tour")

    # post to send_notification with help=0 to ensure no back link is then shown
    assert page.form.attrs["action"] == url_for(
        "main.send_notification",
        service_id=service_one["id"],
        template_id=fake_uuid,
        help="0",
    )


@pytest.mark.parametrize(
    ("template", "recipient", "placeholders", "expected_personalisation"),
    [
        (
            mock_get_service_template,
            "2028675301",
            {"a": "b"},
            {"a": "b"},
        ),
        (
            mock_get_service_email_template,
            "test@example.com",
            {},
            {},
        ),
    ],
)
def test_send_notification_submits_data(
    client_request,
    fake_uuid,
    mock_get_service_template,
    template,
    recipient,
    placeholders,
    expected_personalisation,
    mocker,
    mock_create_job,
):
    mocker.patch("app.main.views.send.s3upload", return_value=sample_uuid())
    with client_request.session_transaction() as session:
        session["recipient"] = recipient
        session["placeholders"] = placeholders

    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )

    mocker.patch("app.main.views.send.check_messages", return_value="")

    client_request.post(
        "main.send_notification", service_id=SERVICE_ONE_ID, template_id=fake_uuid
    )

    mock_create_job.assert_called_once()


def test_send_notification_clears_session(
    client_request,
    service_one,
    fake_uuid,
    mock_send_notification,
    mock_get_service_template,
    mocker,
    mock_create_job,
):
    mocker.patch("app.main.views.send.s3upload", return_value=sample_uuid())
    with client_request.session_transaction() as session:
        session["recipient"] = "2028675301"
        session["placeholders"] = {"a": "b"}

    mocker.patch("app.main.views.send.check_messages")
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )

    client_request.post(
        "main.send_notification", service_id=service_one["id"], template_id=fake_uuid
    )

    with client_request.session_transaction() as session:
        assert "recipient" not in session
        assert "placeholders" not in session


@pytest.mark.parametrize(
    "session_data",
    [
        {"placeholders": {"a": "b"}},  # missing recipient
        {"recipient": "123"},  # missing placeholders
        {"placeholders": {}, "recipient": ""},  # missing address
    ],
)
def test_send_notification_redirects_if_missing_data(
    client_request, fake_uuid, session_data, mocker
):
    with client_request.session_transaction() as session:
        session.update(session_data)

    client_request.post(
        "main.send_notification",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _expected_status=302,
        _expected_redirect=url_for(
            ".send_one_off",
            service_id=SERVICE_ONE_ID,
            template_id=fake_uuid,
        ),
    )


@pytest.mark.parametrize(
    ("extra_args", "extra_redirect_args"), [({}, {}), ({"help": "3"}, {"help": "3"})]
)
def test_send_notification_redirects_to_view_page(
    client_request,
    fake_uuid,
    mock_send_notification,
    mock_get_service_template,
    extra_args,
    extra_redirect_args,
    mocker,
    mock_create_job,
):
    mocker.patch("app.main.views.send.s3upload", return_value=sample_uuid())
    with client_request.session_transaction() as session:
        session["recipient"] = "2028675301"
        session["placeholders"] = {"a": "b"}

    mocker.patch("app.main.views.send.check_messages")

    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )

    client_request.post(
        "main.send_notification",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _expected_status=302,
        **extra_args,
    )


TRIAL_MODE_MSG = (
    "Cannot send to this recipient when service is in trial mode – "
    "see https://www.notifications.service.gov.uk/trial-mode"
)
TOO_LONG_MSG = "Text messages cannot be longer than 918 characters. Your message is 954 characters."
SERVICE_DAILY_LIMIT_MSG = "Exceeded send limits (1000) for today"


@pytest.mark.parametrize(
    ("exception_msg", "expected_h1", "expected_err_details"),
    [
        (
            TRIAL_MODE_MSG,
            "You cannot send to this phone number",
            "In trial mode you can only send to yourself and members of your team",
        ),
        (
            TOO_LONG_MSG,
            "Message too long",
            "Text messages cannot be longer than 918 characters. Your message is 954 characters.",
        ),
        (
            SERVICE_DAILY_LIMIT_MSG,
            "Daily limit reached",
            "You can only send 1,000 messages per day in trial mode.",
        ),
    ],
)
def test_send_notification_shows_error_if_400(
    client_request,
    service_one,
    fake_uuid,
    mocker,
    mock_get_service_template_with_placeholders,
    mock_create_job,
    exception_msg,
    expected_h1,
    expected_err_details,
):
    mocker.patch("app.main.views.send.s3upload", return_value=sample_uuid())

    class MockHTTPError(HTTPError):
        message = exception_msg

    mocker.patch(
        "app.main.views.send.check_messages",
    )

    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )

    mocker.patch(
        "app.notification_api_client.send_notification",
        side_effect=MockHTTPError(),
    )
    with client_request.session_transaction() as session:
        session["recipient"] = "2028675301"
        session["placeholders"] = {"name": "a" * 900}

    # This now redirects to the jobs results page
    page = client_request.post(
        "main.send_notification",
        service_id=service_one["id"],
        template_id=fake_uuid,
        _expected_status=302,
    )

    assert not page.find("input[type=submit]")


def test_send_notification_shows_email_error_in_trial_mode(
    client_request,
    fake_uuid,
    mocker,
    mock_get_service_email_template,
    mock_create_job,
):
    mocker.patch("app.main.views.send.s3upload", return_value=sample_uuid())

    class MockHTTPError(HTTPError):
        message = TRIAL_MODE_MSG
        status_code = 400

    mocker.patch("app.main.views.send.check_messages")
    mocker.patch(
        "app.notification_api_client.get_notifications_for_service",
        return_value=FAKE_ONE_OFF_NOTIFICATION,
    )

    mocker.patch(
        "app.notification_api_client.send_notification",
        side_effect=MockHTTPError(),
    )
    with client_request.session_transaction() as session:
        session["recipient"] = "test@example.com"
        session["placeholders"] = {"date": "foo", "thing": "bar"}

    # Calling this means we successful ran a job so we will be redirect to the jobs page
    client_request.post(
        "main.send_notification",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _expected_status=302,
    )


@pytest.mark.parametrize(
    ("endpoint", "extra_args"),
    [
        ("main.send_one_off_step", {"template_id": uuid4(), "step_index": 0}),
    ],
)
@pytest.mark.parametrize(
    "reply_to_address",
    [
        None,
        uuid4(),
    ],
)
def test_reply_to_is_previewed_if_chosen(
    client_request,
    mocker,
    mock_get_service_email_template,
    mock_get_users_by_service,
    mock_get_service_statistics,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
    get_default_reply_to_email_address,
    fake_uuid,
    endpoint,
    extra_args,
    reply_to_address,
):
    mocker.patch("app.main.views.send.set_metadata_on_csv_upload")

    mocker.patch(
        "app.main.views.send.s3download",
        return_value="""
        email_address,date,thing
        notify@digital.cabinet-office.gov.uk,foo,bar
    """,
    )

    with client_request.session_transaction() as session:
        session["recipient"] = "notify@digital.cabinet-office.gov.uk"
        session["placeholders"] = {}
        session["file_uploads"] = {fake_uuid: {"template_id": fake_uuid}}
        session["sender_id"] = reply_to_address

    page = client_request.get(endpoint, service_id=SERVICE_ONE_ID, **extra_args)

    email_meta = page.select_one(".email-message-meta").text

    if reply_to_address:
        assert "test@example.com" in email_meta
    else:
        assert "test@example.com" not in email_meta


@pytest.mark.parametrize(
    ("endpoint", "extra_args"),
    [
        ("main.check_messages", {"template_id": uuid4(), "upload_id": uuid4()}),
        ("main.send_one_off_step", {"template_id": uuid4(), "step_index": 0}),
    ],
)
@pytest.mark.parametrize(
    "sms_sender",
    [
        None,
        uuid4(),
    ],
)
def test_sms_sender_is_previewed(
    client_request,
    mocker,
    mock_get_service_template,
    mock_get_users_by_service,
    mock_get_service_statistics,
    mock_get_job_doesnt_exist,
    mock_get_jobs,
    get_default_sms_sender,
    fake_uuid,
    endpoint,
    extra_args,
    sms_sender,
):

    mocker.patch("app.main.views.send.set_metadata_on_csv_upload")

    mocker.patch(
        "app.main.views.send.get_csv_metadata",
        return_value={"original_file_name": "example.csv"},
    )
    mocker.patch(
        "app.main.views.send.s3download",
        return_value="""
        phone number,date,thing
        2028675109,foo,bar
    """,
    )

    with client_request.session_transaction() as session:
        session["recipient"] = "2028675109"
        session["placeholders"] = {}
        session["file_uploads"] = {
            fake_uuid: {
                "template_id": fake_uuid,
                "notification_count": 1,
                "valid": True,
            }
        }
        session["sender_id"] = sms_sender

    page = client_request.get(endpoint, service_id=SERVICE_ONE_ID, **extra_args)

    sms_sender_on_page = page.select_one(".sms-message-sender")

    if sms_sender:
        assert sms_sender_on_page.text.strip() == "From: GOVUK"
    else:
        assert not sms_sender_on_page


def test_redirects_to_template_if_job_exists_already(
    client_request,
    mock_get_service_email_template,
    mock_get_job,
    fake_uuid,
):
    client_request.get(
        "main.check_messages",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        upload_id=fake_uuid,
        original_file_name="example.csv",
        _expected_status=301,
        _expected_redirect=url_for(
            "main.send_messages",
            service_id=SERVICE_ONE_ID,
            template_id=fake_uuid,
        ),
    )


def test_send_to_myself_sets_placeholder_and_redirects_for_email(
    mocker, client_request, fake_uuid, mock_get_service_email_template
):
    with client_request.session_transaction() as session:
        session["recipient"] = None
        session["placeholders"] = {}

    client_request.get(
        "main.send_one_off_to_myself",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _expected_status=302,
        _expected_url=url_for(
            "main.send_one_off_step",
            service_id=SERVICE_ONE_ID,
            template_id=fake_uuid,
            step_index=1,
        ),
    )

    with client_request.session_transaction() as session:
        assert session["recipient"] == "test@user.gsa.gov"
        assert session["placeholders"] == {"email address": "test@user.gsa.gov"}


def test_send_to_myself_sets_placeholder_and_redirects_for_sms(
    mocker, client_request, fake_uuid, mock_get_service_template
):
    with client_request.session_transaction() as session:
        session["recipient"] = None
        session["placeholders"] = {}

    client_request.get(
        "main.send_one_off_to_myself",
        service_id=SERVICE_ONE_ID,
        template_id=fake_uuid,
        _expected_status=302,
        _expected_url=url_for(
            "main.send_one_off_step",
            service_id=SERVICE_ONE_ID,
            template_id=fake_uuid,
            step_index=1,
        ),
    )

    with client_request.session_transaction() as session:
        assert session["recipient"] == "202-867-5303"
        assert session["placeholders"] == {"phone number": "202-867-5303"}
