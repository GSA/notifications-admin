import pytest

from app.utils.redis_util import add_row_data_to_redis


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
    mock_redis = mocker.patch("app.extensions.RedisClient.set")

    add_row_data_to_redis(data, job_id)

    mock_redis.assert_called_with(expected_key, expected_val)
