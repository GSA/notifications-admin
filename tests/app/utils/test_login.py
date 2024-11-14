import pytest
from freezegun import freeze_time

from app.models.user import User
from app.utils.login import email_needs_revalidating


@freeze_time("2020-11-27T12:00:00")
@pytest.mark.parametrize(
    ("email_access_validated_at", "expected_result"),
    [
        ("2020-10-01T11:35:21.726132Z", False),
        ("2020-07-23T11:35:21.726132Z", True),
    ],
)
def test_email_needs_revalidating(
    api_user_active,
    email_access_validated_at,
    expected_result,
):
    api_user_active["email_access_validated_at"] = email_access_validated_at
    assert email_needs_revalidating(User(api_user_active)) == expected_result


def test_get_id_token(mocker):
    mock_request_get = mocker.patch("requests.get")
    fake_kid = "fake"
    mock_request_get.return_value.json.return_value = {
        "keys": [{"kid": fake_kid, "alg": "whatever"}]
    }
    mock_dumps = mocker.patch("json.dumps")
    mock_dumps.return_value = "Not really JSON"
    mock_from_jwk = mocker.patch("jwt.algorithms.RSAAlgorithm.from_jwk")
    mock_from_jwk.return_value = "Fake fake fake"
    mock_get_unverified_header = mocker.patch("jwt.get_unverified_header")
    mock_get_unverified_header.return_value.__getitem__.return_value = fake_kid
    mock_decode = mocker.patch("jwt.decode")
    from app.utils import login

    login.get_id_token({"id_token": "Not a token"})

    assert mock_decode.called
