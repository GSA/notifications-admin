import pytest
from bs4 import BeautifulSoup

from app.utils.pagination import get_page_from_request
from tests.conftest import SERVICE_ONE_ID

MOCK_JOBS = {
    "data": [
        {
            "archived": False,
            "created_at": "2024-01-04T20:43:52+00:00",
            "created_by": {
                "id": "mocked_user_id",
                "name": "mocked_user",
            },
            "id": "55b242b5-9f62-4271-aff7-039e9c320578",
            "job_status": "finished",
            "notification_count": 1,
            "original_file_name": "mocked_file.csv",
            "processing_finished": "2024-01-25T23:02:25+00:00",
            "processing_started": "2024-01-25T23:02:24+00:00",
            "scheduled_for": None,
            "service": "21b3ee3d-1cb0-4666-bfa0-9c5ac26d3fe3",
            "service_name": {"name": "Mock Texting Service"},
            "statistics": [
                {"count": 1, "status": "delivered"},
                {"count": 5, "status": "failed"},
            ],
            "template": "6a456418-498c-4c86-b0cd-9403c14a216c",
            "template_name": "Mock Template Name",
            "template_type": "sms",
            "template_version": 3,
            "updated_at": "2024-01-25T23:02:25+00:00",
        }
    ],
    "links": {
        "last": "/service/21b3ee3d-1cb0-4666-bfa0-9c5ac26d3fe3/job?page=3",
        "next": "/service/21b3ee3d-1cb0-4666-bfa0-9c5ac26d3fe3/job?page=3",
        "prev": "/service/21b3ee3d-1cb0-4666-bfa0-9c5ac26d3fe3/job?page=1",
    },
    "page_size": 50,
    "total": 115,
}


def test_all_activity(
    client_request,
    mocker,
):
    current_page = get_page_from_request()
    mock_get_page_of_jobs = mocker.patch(
        "app.job_api_client.get_page_of_jobs", return_value=MOCK_JOBS
    )
    mocker.patch("app.job_api_client.get_immediate_jobs", return_value=[])
    mock_s3_obj = mocker.Mock()
    mock_s3_obj.content_length = 0
    mocker.patch("app.s3_client.get_s3_object", return_value=mock_s3_obj)
    mocker.patch("app.s3_client.check_s3_file_exists", return_value=False)
    mocker.patch("app.s3_client.s3_csv_client.get_csv_upload", return_value=None)

    response = client_request.get_response(
        "main.all_jobs_activity",
        service_id=SERVICE_ONE_ID,
        page=current_page,
    )
    assert response.status_code == 200, "Request failed"
    assert response.data is not None, "Response data is None"

    assert "All activity" in response.text

    assert any(
        call[0][0] == SERVICE_ONE_ID and call[1].get("page") == current_page
        for call in mock_get_page_of_jobs.call_args_list
    )
    page = BeautifulSoup(response.data, "html.parser")
    table = page.find("table")
    assert table is not None, "Table not found in the response"

    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    expected_headers = [
        "Job ID#",
        "Template",
        "Started",
        "Sender",
        "Report",
        "Status",
    ]

    assert (
        headers == expected_headers
    ), f"Expected headers {expected_headers}, but got {headers}"

    rows = table.find("tbody").find_all("tr", class_="table-row")
    assert len(rows) == 1, "Expected one job row in the table"

    job_row = rows[0]
    cells = job_row.find_all("td")
    assert len(cells) == 6, "Expected six columns in the job row"

    job_id_cell = cells[0].find("a").get_text(strip=True)

    assert (
        job_id_cell == "55b242b5"
    ), f"Expected job ID '55b242b5', but got '{job_id_cell}'"
    template_cell = cells[1].get_text(strip=True)
    assert (
        template_cell == "Mock Template Name"
    ), f"Expected template 'Mock Template Name', but got '{template_cell}'"
    time_sent_cell = cells[2].get_text(strip=True)
    assert (
        time_sent_cell == "01-25-2024 at 06:02 PM"
    ), f"Expected time sent '01-25-2024 at 06:02 PM', but got '{time_sent_cell}'"
    sender_cell = cells[3].get_text(strip=True)
    assert (
        sender_cell == "mocked_user"
    ), f"Expected sender 'mocked_user', but got '{sender_cell}'"

    report_cell = cells[4].find("span").get_text(strip=True)
    assert report_cell == "N/A", f"Expected report 'N/A', but got '{report_cell}'"

    status_cell = cells[5].get_text(strip=True)
    assert (
        "1 delivered" in status_cell
    ), f"Expected status to contain '1 delivered', but got '{status_cell}'"
    assert (
        "5 failed" in status_cell
    ), f"Expected status to contain '5 failed', but got '{status_cell}'"


def test_all_activity_no_jobs(client_request, mocker):
    current_page = get_page_from_request()
    mock_get_page_of_jobs = mocker.patch(
        "app.job_api_client.get_page_of_jobs",
        return_value={
            "data": [],
            "links": {
                "last": "/service/21b3ee3d-1cb0-4666-bfa0-9c5ac26d3fe3/job?page=1",
                "next": None,
                "prev": None,
            },
            "page_size": 50,
            "total": 0,
        },
    )
    mocker.patch("app.job_api_client.get_immediate_jobs", return_value=[])
    mock_s3_obj = mocker.Mock()
    mock_s3_obj.content_length = 0
    mocker.patch("app.s3_client.get_s3_object", return_value=mock_s3_obj)
    mocker.patch("app.s3_client.check_s3_file_exists", return_value=False)
    mocker.patch("app.s3_client.s3_csv_client.get_csv_upload", return_value=None)
    response = client_request.get_response(
        "main.all_jobs_activity",
        service_id=SERVICE_ONE_ID,
        page=current_page,
    )

    assert response.status_code == 200, "Request failed"

    page = BeautifulSoup(response.data, "html.parser")

    no_jobs_message_td = page.find("td", class_="table-empty-message")
    assert no_jobs_message_td is not None, "No jobs message not found in the response"

    expected_message = "No messages found"
    actual_message = no_jobs_message_td.get_text(strip=True)

    assert (
        expected_message == actual_message
    ), f"Expected message '{expected_message}', but got '{actual_message}'"
    assert any(
        call[0][0] == SERVICE_ONE_ID and call[1].get("page") == current_page
        for call in mock_get_page_of_jobs.call_args_list
    )


def test_all_activity_pagination(client_request, mocker):
    current_page = get_page_from_request()
    mock_get_page_of_jobs = mocker.patch(
        "app.job_api_client.get_page_of_jobs",
        return_value={
            "data": [
                {
                    "id": f"job-{i}",
                    "created_at": "2024-01-25T23:02:25+00:00",
                    "created_by": {"name": "mocked_user"},
                    "processing_finished": "2024-01-25T23:02:25+00:00",
                    "processing_started": "2024-01-25T23:02:24+00:00",
                    "template_name": "Mock Template Name",
                    "original_file_name": "mocked_file.csv",
                    "notification_count": 1,
                }
                for i in range(1, 101)
            ],
            "links": {
                "last": "/service/21b3ee3d-1cb0-4666-bfa0-9c5ac26d3fe3/job?page=2",
                "next": "/service/21b3ee3d-1cb0-4666-bfa0-9c5ac26d3fe3/job?page=2",
                "prev": None,
            },
            "page_size": 50,
            "total": 100,
        },
    )
    mocker.patch("app.job_api_client.get_immediate_jobs", return_value=[])
    mock_s3_obj = mocker.Mock()
    mock_s3_obj.content_length = 0
    mocker.patch("app.s3_client.get_s3_object", return_value=mock_s3_obj)
    mocker.patch("app.s3_client.check_s3_file_exists", return_value=False)
    mocker.patch("app.s3_client.s3_csv_client.get_csv_upload", return_value=None)

    response = client_request.get_response(
        "main.all_jobs_activity",
        service_id=SERVICE_ONE_ID,
        page=current_page,
    )
    assert any(
        call[0][0] == SERVICE_ONE_ID and call[1].get("page") == current_page
        for call in mock_get_page_of_jobs.call_args_list
    )

    page = BeautifulSoup(response.data, "html.parser")
    pagination_controls = page.find_all("li", class_="usa-pagination__item")
    assert pagination_controls, "Pagination controls not found in the response"

    pagination_texts = [item.get_text(strip=True) for item in pagination_controls]
    expected_pagination_texts = ["1", "2", "Next"]
    assert (
        pagination_texts == expected_pagination_texts
    ), f"Expected pagination controls {expected_pagination_texts}, but got {pagination_texts}"


@pytest.mark.parametrize(
    ("filter_type", "expected_limit_days"),
    [
        ("24hours", 1),
        ("3days", 3),
        ("7days", 7),
        (None, None),
    ],
)
def test_all_activity_filters(client_request, mocker, filter_type, expected_limit_days):
    current_page = get_page_from_request()
    mock_get_page_of_jobs = mocker.patch(
        "app.job_api_client.get_page_of_jobs", return_value=MOCK_JOBS
    )
    mocker.patch("app.job_api_client.get_immediate_jobs", return_value=[])
    mock_s3_obj = mocker.Mock()
    mock_s3_obj.content_length = 0
    mocker.patch("app.s3_client.get_s3_object", return_value=mock_s3_obj)
    mocker.patch("app.s3_client.check_s3_file_exists", return_value=False)
    mocker.patch("app.s3_client.s3_csv_client.get_csv_upload", return_value=None)

    kwargs = {"filter": filter_type} if filter_type else {}
    response = client_request.get_response(
        "main.all_jobs_activity", service_id=SERVICE_ONE_ID, page=current_page, **kwargs
    )

    assert response.status_code == 200
    assert "All activity" in response.text

    if expected_limit_days:
        mock_get_page_of_jobs.assert_any_call(
            SERVICE_ONE_ID,
            page=current_page,
            limit_days=expected_limit_days,
            use_processing_time=True,
        )
    else:
        mock_get_page_of_jobs.assert_any_call(SERVICE_ONE_ID, page=current_page)


def test_download_links_show_when_data_available(
    client_request,
    service_one,
    active_user_with_permissions,
    mocker,
):

    mock_jobs_with_data = {
        "data": [{"id": "job1", "created_at": "2020-01-01T00:00:00.000000+00:00"}],
        "total": 1,
        "page_size": 50,
    }

    mocker.patch(
        "app.job_api_client.get_page_of_jobs", return_value=mock_jobs_with_data
    )
    mocker.patch("app.job_api_client.get_immediate_jobs", return_value=[{"id": "job1"}])
    mocker.patch("app.s3_client.check_s3_file_exists", return_value=True)
    mock_obj = mocker.Mock()
    mock_obj.content_length = 1024
    mocker.patch("app.s3_client.get_s3_object", return_value=mock_obj)
    mocker.patch("app.s3_client.s3_csv_client.get_csv_upload", return_value=mock_obj)

    page = client_request.get(
        "main.all_jobs_activity",
        service_id=service_one["id"],
    )

    assert "Download recent reports" in page.text
    assert "Yesterday" in page.text
    assert "Last 3 days" in page.text
    assert "Last 5 days" in page.text
    assert "Last 7 days" in page.text


def test_download_links_partial_data_available(
    client_request,
    service_one,
    active_user_with_permissions,
    mocker,
):
    mock_jobs_with_data = {
        "data": [{"id": "job1", "created_at": "2020-01-01T00:00:00.000000+00:00"}],
        "total": 1,
        "page_size": 50,
    }
    mock_jobs_empty = {"data": [], "total": 0, "page_size": 50}

    def mock_get_page_of_jobs(service_id, page=1, limit_days=None):
        if limit_days in [1, 5]:
            return mock_jobs_with_data
        return mock_jobs_empty

    mocker.patch(
        "app.job_api_client.get_page_of_jobs", side_effect=mock_get_page_of_jobs
    )
    mocker.patch("app.job_api_client.get_immediate_jobs", return_value=[])
    mocker.patch("app.s3_client.check_s3_file_exists", return_value=True)
    mock_obj = mocker.Mock()
    mock_obj.content_length = 2048
    mocker.patch("app.s3_client.s3_csv_client.get_csv_upload", return_value=mock_obj)
    mocker.patch("app.s3_client.get_s3_object", return_value=mock_obj)

    page = client_request.get(
        "main.all_jobs_activity",
        service_id=service_one["id"],
    )

    assert "Download recent reports" in page.text
    assert "Yesterday" in page.text
    assert "Last 3 days" in page.text
    assert "Last 5 days" in page.text
    assert "Last 7 days" in page.text
    assert "No recent activity to download" not in page.text


def test_download_links_no_data_available(
    client_request,
    service_one,
    active_user_with_permissions,
    mocker,
):
    mock_jobs_empty = {"data": [], "total": 0, "page_size": 50}

    mocker.patch("app.job_api_client.get_page_of_jobs", return_value=mock_jobs_empty)
    mocker.patch("app.job_api_client.get_immediate_jobs", return_value=[])
    mocker.patch("app.s3_client.check_s3_file_exists", return_value=False)
    mock_obj = mocker.Mock()
    mock_obj.content_length = 0
    mocker.patch("app.s3_client.get_s3_object", return_value=mock_obj)

    page = client_request.get(
        "main.all_jobs_activity",
        service_id=service_one["id"],
    )

    assert "Download recent reports" in page.text
    assert "Yesterday" in page.text
    assert "No messages sent" in page.text
    assert "Last 3 days - No messages sent" in page.text
    assert "Last 5 days - No messages sent" in page.text
    assert "Last 7 days - No messages sent" in page.text


def test_download_not_available_to_users_without_dashboard(
    client_request,
    active_caseworking_user,
):
    client_request.login(active_caseworking_user)
    client_request.get(
        "main.download_notifications_csv",
        service_id=SERVICE_ONE_ID,
        _expected_status=403,
    )
