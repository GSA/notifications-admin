from freezegun import freeze_time

from tests.conftest import normalize_spaces


@freeze_time("2016-12-12 12:00:00.000000")
def test_get_support_as_someone_in_the_public_sector(
    mocker,
    active_user_with_permissions,
    client_request,
):
    page = client_request.get(
        "main.support",
    )
    assert normalize_spaces(page.select("h1")) == ("Contact us")
