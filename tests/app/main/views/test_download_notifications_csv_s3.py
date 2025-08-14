import pytest
from unittest.mock import patch

from app.main.views.notifications import (
    PERIOD_TO_S3_FILENAME,
    generate_empty_report_csv,
)
from notifications_utils.s3 import S3ObjectNotFound
from tests.conftest import SERVICE_ONE_ID


def test_period_to_s3_filename_mapping():
    assert PERIOD_TO_S3_FILENAME["one_day"] == "1-day-report"
    assert PERIOD_TO_S3_FILENAME["three_day"] == "3-day-report"
    assert PERIOD_TO_S3_FILENAME["five_day"] == "5-day-report"
    assert PERIOD_TO_S3_FILENAME["seven_day"] == "7-day-report"


def test_empty_csv_has_correct_headers():
    result = list(generate_empty_report_csv())
    assert len(result) == 1
    assert "Phone Number,Template,Sent by,Batch File" in result[0]


@patch("app.main.views.notifications.s3download")
@patch("app.main.views.notifications.generate_notifications_csv")
def test_job_based_reports_dont_use_s3(
    mock_generate_csv,
    mock_s3download,
    client_request,
    service_one,
    mock_get_service_data_retention,
):
    mock_generate_csv.return_value = iter(["test,data\n"])

    response = client_request.get_response(
        "main.download_notifications_csv",
        service_id=SERVICE_ONE_ID,
        number_of_days="one_day",
        message_type="sms",
        job_id="test-job-123",
        _test_page_title=False,
    )

    mock_s3download.assert_not_called()
    mock_generate_csv.assert_called_once()
    assert response.status_code == 200


@patch("app.main.views.notifications.s3download")
@patch("app.main.views.notifications.generate_notifications_csv")
def test_general_reports_use_s3(
    mock_generate_csv,
    mock_s3download,
    client_request,
    service_one,
    mock_get_service_data_retention,
):
    mock_s3download.return_value = b"s3,csv,content\n"

    response = client_request.get_response(
        "main.download_notifications_csv",
        service_id=SERVICE_ONE_ID,
        number_of_days="three_day",
        message_type="sms",
        _test_page_title=False,
    )

    mock_s3download.assert_called_once_with(SERVICE_ONE_ID, "3-day-report")
    mock_generate_csv.assert_not_called()
    assert response.status_code == 200


@patch("app.main.views.notifications.s3download")
def test_missing_s3_file_returns_headers_only(
    mock_s3download,
    client_request,
    service_one,
    mock_get_service_data_retention,
):
    mock_s3download.side_effect = S3ObjectNotFound(
        {"Error": {"Code": "NoSuchKey"}}, "GetObject"
    )

    response = client_request.get_response(
        "main.download_notifications_csv",
        service_id=SERVICE_ONE_ID,
        number_of_days="five_day",
        message_type="sms",
        _test_page_title=False,
    )

    assert response.status_code == 200
    assert b"Phone Number,Template,Sent by" in response.data
    assert response.data.count(b"\n") == 1


@patch("app.main.views.notifications.convert_s3_csv_timestamps")
@patch("app.main.views.notifications.s3download")
def test_s3_csv_gets_timezone_converted(
    mock_s3download,
    mock_convert,
    client_request,
    service_one,
    mock_get_service_data_retention,
):
    mock_s3download.return_value = b"csv,data"
    mock_convert.return_value = iter(["converted,csv,data\n"])

    response = client_request.get_response(
        "main.download_notifications_csv",
        service_id=SERVICE_ONE_ID,
        number_of_days="three_day",
        message_type="sms",
        _test_page_title=False,
    )

    mock_convert.assert_called_once_with(b"csv,data")
    assert response.status_code == 200
