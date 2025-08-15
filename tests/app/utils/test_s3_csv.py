from unittest.mock import patch

from app.utils.s3_csv import convert_s3_csv_timestamps


def test_convert_s3_csv_timestamps_with_real_format():
    s3_csv_content = (
        "Phone Number,Template,Sent By,Carrier,Status,Time,Batch File,Carrier Response\n"
        "14254147167,Example text message template,Backstop Test User,,Failed,"
        "2024-03-15 17:19:00,one-off-f0b91c0f.csv,Phone has blocked SMS\n"
        "14254147755,Example text message template,Admin User,,Delivered,"
        "2024-03-15 20:30:00,batch1.csv,Success"
    )

    with patch(
        "app.utils.s3_csv.convert_report_date_to_preferred_timezone"
    ) as mock_convert:

        def mock_conversion(timestamp):
            # Just return the timestamp as-is for testing
            return timestamp

        mock_convert.side_effect = mock_conversion

        result = list(convert_s3_csv_timestamps(s3_csv_content))
        full_result = "".join(result)

        assert (
            "Phone Number,Template,Sent By,Carrier,Status,Time,Batch File,Carrier Response"
            in result[0]
        )
        assert mock_convert.call_count == 2
        mock_convert.assert_any_call("2024-03-15 17:19:00")
        mock_convert.assert_any_call("2024-03-15 20:30:00")
        assert "2024-03-15 17:19:00" in full_result
        assert "2024-03-15 20:30:00" in full_result


def test_convert_s3_csv_handles_empty_csv():
    result = list(convert_s3_csv_timestamps(""))
    assert result == []


def test_convert_s3_csv_handles_headers_only():
    csv_content = "Phone Number,Template,Sent by,Batch File,Carrier Response,Status,Time,Carrier\n"
    result = list(convert_s3_csv_timestamps(csv_content))
    assert len(result) == 1
    assert "Phone Number,Template" in result[0]


def test_convert_s3_csv_handles_bytes():
    csv_bytes = (
        b"Phone Number,Template,Sent by,Batch File,Carrier Response,Status,Time,Carrier\n"
        b"+12025551234,Test,John,,Success,delivered,2024-01-15 20:30:00,Verizon"
    )

    with patch(
        "app.utils.s3_csv.convert_report_date_to_preferred_timezone"
    ) as mock_convert:
        mock_convert.return_value = "2024-01-15 15:30:00"

        result = list(convert_s3_csv_timestamps(csv_bytes))
        assert len(result) == 2
        assert mock_convert.called


def test_convert_s3_csv_handles_malformed_dates():
    csv_content = """Phone Number,Template,Sent by,Batch File,Carrier Response,Status,Time,Carrier
+12025551234,Test,John,,Success,delivered,INVALID_DATE,Verizon
+12025555678,Test,Jane,,Success,delivered,2024-01-15 21:45:00,AT&T"""

    with patch(
        "app.utils.s3_csv.convert_report_date_to_preferred_timezone"
    ) as mock_convert:
        mock_convert.side_effect = [
            Exception("Invalid date"),
            "2024-01-15 16:45:00",
        ]

        result = list(convert_s3_csv_timestamps(csv_content))
        full_result = "".join(result)

        assert "INVALID_DATE" in full_result
        assert "2024-01-15 16:45:00" in full_result


def test_finds_time_column_dynamically():
    csv_content = """Template,Phone Number,Time,Status
Test Template,+12025551234,2024-01-15 20:30:00,delivered
Another Template,+12025555678,2024-01-15 21:45:00,delivered"""

    with patch(
        "app.utils.s3_csv.convert_report_date_to_preferred_timezone"
    ) as mock_convert:
        mock_convert.side_effect = lambda x: f"{x} Converted"

        result = list(convert_s3_csv_timestamps(csv_content))
        full_result = "".join(result)

        assert mock_convert.call_count == 2
        assert "2024-01-15 20:30:00 Converted" in full_result
        assert "2024-01-15 21:45:00 Converted" in full_result


def test_actual_timezone_conversion():
    from app.utils.csv import convert_report_date_to_preferred_timezone

    with patch("app.utils.csv.current_user") as mock_user:
        mock_user.preferred_timezone = "US/Eastern"

        result = convert_report_date_to_preferred_timezone("2024-01-15 20:30:00")

        # Should be in 24-hour format without AM/PM or timezone
        assert "15:30:00" in result
        assert "PM" not in result
        assert "US/Eastern" not in result
