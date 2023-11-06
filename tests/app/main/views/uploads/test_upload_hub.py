import pytest
from freezegun import freeze_time

from app.formatters import normalize_spaces
from tests.conftest import (
    SERVICE_ONE_ID,
    create_active_caseworking_user,
    create_active_user_with_permissions,
)


@pytest.mark.usefixtures("_mock_get_no_uploads")
@pytest.mark.parametrize(
    ("extra_permissions", "expected_empty_message"),
    [
        ([], ("You have not uploaded any files recently.")),
    ],
)
def test_get_upload_hub_with_no_uploads(
    mocker,
    client_request,
    service_one,
    extra_permissions,
    expected_empty_message,
):
    mocker.patch("app.job_api_client.get_jobs", return_value={"data": []})
    service_one["permissions"] += extra_permissions
    page = client_request.get("main.uploads", service_id=SERVICE_ONE_ID)
    assert (
        normalize_spaces(
            " ".join(paragraph.text for paragraph in page.select("main p"))
        )
        == expected_empty_message
    )
    assert not page.select(".file-list-filename")


@freeze_time("2017-10-10 10:10:10")
def test_get_upload_hub_page(
    mocker,
    client_request,
    service_one,
    mock_get_uploads,
):
    mocker.patch("app.job_api_client.get_jobs", return_value={"data": []})
    page = client_request.get("main.uploads", service_id=SERVICE_ONE_ID)
    assert page.find("h1").text == "Uploads"

    uploads = page.select("tbody tr")

    assert len(uploads) == 1

    assert normalize_spaces(uploads[0].text.strip()) == (
        "some.csv " "Sent 1 January 2016 at 11:09 UTC " "0 pending 8 delivered 2 failed"
    )
    assert uploads[0].select_one("a.file-list-filename-large")["href"] == (
        "/services/{}/jobs/job_id_1".format(SERVICE_ONE_ID)
    )


@pytest.mark.usefixtures("_mock_get_no_uploads")
@pytest.mark.parametrize(
    "user",
    [
        create_active_caseworking_user(),
        create_active_user_with_permissions(),
    ],
)
@freeze_time("2012-12-12 12:12")
def test_uploads_page_shows_scheduled_jobs(
    mocker,
    client_request,
    mock_get_jobs,
    user,
):
    client_request.login(user)
    page = client_request.get("main.uploads", service_id=SERVICE_ONE_ID)

    assert [normalize_spaces(row.text) for row in page.select("tr")] == [
        ("File Status"),
        (
            "even_later.csv "
            "Sending 1 January 2016 at 23:09 UTC "
            "1 text message waiting to send"
        ),
        (
            "send_me_later.csv "
            "Sending 1 January 2016 at 11:09 UTC "
            "1 text message waiting to send"
        ),
    ]
    assert not page.select(".table-empty-message")
