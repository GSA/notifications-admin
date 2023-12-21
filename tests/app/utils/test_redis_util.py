import pytest

from app.utils.redis_util import add_row_data_to_redis, get_csv_row, get_phone_number


@pytest.mark.parametrize(
    ("data", "job_id", "expected_key", "expected_val"),
    [
        (
            "phone number\r\n15555555555",
            "aaa",
            "job_aaa_row_0_phone_number",
            "15555555555",
        ),
        (
            "ssn,phone number\r\n555-55-5555,15556666666",
            "bbb",
            "job_bbb_row_0_phone_number",
            "15556666666",
        ),
    ],
)
def test_add_data_to_redis(mocker, data, job_id, expected_key, expected_val):
    mock_redis_set = mocker.patch("app.extensions.RedisClient.set")

    add_row_data_to_redis(data, job_id)

    mock_redis_set.assert_called_with(expected_key, expected_val)


@pytest.mark.parametrize(
    ("data", "job_id", "expected_key", "expected_val"),
    [
        (
            "phone number\r\n15555555555",
            "aaa",
            "job_aaa_row_0_phone_number",
            "15555555555",
        ),
        (
            "ssn,phone number\r\n555-55-5555,15556666666",
            "bbb",
            "job_bbb_row_0_phone_number",
            "15556666666",
        ),
    ],
)
def test_get_phone_number(mocker, data, job_id, expected_key, expected_val):
    mock_redis_get = mocker.patch(
        "app.extensions.RedisClient.get", return_value=expected_val
    )

    phone_number = get_phone_number(job_id, 0)

    mock_redis_get.assert_called_with(f"job_{job_id}_row_0_phone_number")
    assert phone_number == expected_val


@pytest.mark.parametrize(
    (
        "data",
        "job_id",
        "expected_key",
        "expected_val",
        "expected_columns",
        "expected_raw_row",
    ),
    [
        (
            "phone number\r\n15555555555",
            "aaa",
            "job_aaa_row_0",
            {"phone number": "15555555555"},
            "phone number",
            "15555555555",
        ),
        (
            "ssn,phone number\r\n555-55-5555,15556666666",
            "bbb",
            "job_bbb_row_0r",
            {"ssn": "555-55-5555", "phone number": "15556666666"},
            "ssn,phone number",
            "555-55-5555,15556666666",
        ),
    ],
)
def test_get_csv_row(
    mocker, data, job_id, expected_key, expected_val, expected_columns, expected_raw_row
):
    mock_redis_get = mocker.patch(
        "app.extensions.RedisClient.get", side_effect=[expected_raw_row, expected_val]
    )

    mock_column_headers = mocker.patch(
        "app.utils.redis_util.get_csv_column_headers", return_value=expected_columns
    )

    csv_row = get_csv_row(job_id, 0)
    mock_column_headers.assert_called_with(job_id)

    mock_redis_get.assert_called_with(f"job_{job_id}_row_0")
    assert csv_row == expected_val
