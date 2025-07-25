import pytest
from flask import url_for
from freezegun import freeze_time

from app.utils.user import is_gov_user
from notifications_python_client.errors import HTTPError
from tests import organization_json


def test_non_gov_user_cannot_see_add_service_button(
    client_request,
    mock_login,
    mock_get_non_govuser,
    api_nongov_user_active,
    mock_get_organizations,
    mock_get_organizations_and_services_for_user,
):
    client_request.login(api_nongov_user_active)
    page = client_request.get("main.choose_account")
    assert "Add a new service" not in page.text


@pytest.mark.parametrize(
    "org_json",
    [
        None,
        organization_json(organization_type=None),
    ],
)
def test_get_should_render_add_service_template(
    client_request,
    mocker,
    org_json,
    platform_admin_user,
):
    client_request.login(platform_admin_user)
    mocker.patch(
        "app.organizations_client.get_organization_by_domain",
        return_value=org_json,
    )
    page = client_request.get("main.add_service")
    assert page.select_one("h1").text.strip() == "About your service"
    assert page.select_one("input[name=name]").get("value") is None


def test_get_should_not_render_radios_if_org_type_known(
    client_request, mocker, platform_admin_user
):
    client_request.login(platform_admin_user)
    mocker.patch(
        "app.organizations_client.get_organization_by_domain",
        return_value=organization_json(organization_type="central"),
    )
    page = client_request.get("main.add_service")
    assert page.select_one("h1").text.strip() == "About your service"
    assert page.select_one("input[name=name]").get("value") is None
    assert not page.select(".usa-radio")


def test_show_different_page_if_user_org_type_is_local(
    client_request, mocker, platform_admin_user
):
    client_request.login(platform_admin_user)
    mocker.patch(
        "app.organizations_client.get_organization_by_domain",
        return_value=organization_json(organization_type="local"),
    )
    page = client_request.get("main.add_service")
    assert page.select_one("h1").text.strip() == "About your service"
    assert page.select_one("input[name=name]").get("value") is None
    assert page.select_one("main .usa-body").text.strip() == (
        "Give your service a name that tells users what your "
        "messages are about, as well as who they’re from. For example:"
    )


@pytest.mark.parametrize(
    "email_address",
    [
        # User’s email address doesn’t matter when the organization is known
        "test@example.gsa.gov",
        "test@anotherexample.gsa.gov",
    ],
)
@pytest.mark.parametrize(
    ("inherited", "posted", "persisted", "sms_limit"),
    [
        (None, "federal", "federal", 150_000),
        # ('federal', None, 'federal', 150_000),
    ],
)
@freeze_time("2021-01-01")
def test_should_add_service_and_redirect_to_tour_when_no_services(
    mocker,
    client_request,
    mock_create_service,
    mock_create_service_template,
    mock_get_services_with_no_services,
    api_user_active,
    inherited,
    email_address,
    posted,
    persisted,
    sms_limit,
    platform_admin_user,
):
    api_user_active["email_address"] = email_address
    client_request.login(platform_admin_user)
    mocker.patch(
        "app.organizations_client.get_organization_by_domain",
        return_value=organization_json(organization_type=inherited),
    )
    client_request.post(
        "main.add_service",
        _data={
            "name": "testing the post",
            "organization_type": posted,
        },
        _expected_status=302,
        _expected_redirect=url_for(
            "main.begin_tour",
            service_id=101,
            template_id="Example%20text%20message%20template",
        ),
    )
    assert mock_get_services_with_no_services.called
    mock_create_service.assert_called_once_with(
        service_name="testing the post",
        organization_type=persisted,
        message_limit=50,
        restricted=True,
        user_id=api_user_active["id"],
        email_from="testing.the.post",
    )
    mock_create_service_template.assert_called_once_with(
        "Example text message template",
        "sms",
        (
            "Hi, I’m trying out Notify.gov. Today is "
            "((day of week)) and my favorite color is ((color))."
        ),
        101,
    )
    with client_request.session_transaction() as session:
        assert session["service_id"] == 101


def test_add_service_has_to_choose_org_type(
    mocker,
    client_request,
    mock_create_service,
    mock_create_service_template,
    mock_get_services_with_no_services,
    api_user_active,
    platform_admin_user,
):
    client_request.login(platform_admin_user)
    mocker.patch(
        "app.organizations_client.get_organization_by_domain",
        return_value=None,
    )
    client_request.post(
        "main.add_service",
        _data={
            "name": "testing the post",
        },
        _expected_status=302,
    )
    assert mock_create_service.called is True
    assert mock_create_service_template.called is True


@pytest.mark.parametrize(
    "email_address",
    [
        "test@nhs.net",
        "test@nhs.uk",
        "test@example.NhS.uK",
        "test@EXAMPLE.NHS.NET",
    ],
)
@pytest.mark.skip(reason="Update for TTS")
def test_get_should_only_show_nhs_org_types_radios_if_user_has_nhs_email(
    client_request,
    mocker,
    api_user_active,
    email_address,
):
    api_user_active["email_address"] = email_address
    client_request.login(api_user_active)
    mocker.patch(
        "app.organizations_client.get_organization_by_domain",
        return_value=None,
    )
    page = client_request.get("main.add_service")
    assert page.select_one("h1").text.strip() == "About your service"
    assert page.select_one("input[name=name]").get("value") is None
    assert [label.text.strip() for label in page.select(".usa-radio label")] == [
        "NHS – central government agency or public body",
        "NHS Trust or Clinical Commissioning Group",
        "GP practice",
    ]
    assert [radio["value"] for radio in page.select(".usa-radio input")] == [
        "nhs_central",
        "nhs_local",
        "nhs_gp",
    ]


@pytest.mark.parametrize(
    ("organization_type", "free_allowance"),
    [
        ("federal", 150_000),
        ("state", 150_000),
    ],
)
def test_should_add_service_and_redirect_to_dashboard_when_existing_service(
    notify_admin,
    mocker,
    client_request,
    mock_create_service,
    mock_create_service_template,
    mock_get_services,
    mock_get_no_organization_by_domain,
    api_user_active,
    organization_type,
    free_allowance,
    platform_admin_user,
):
    client_request.login(platform_admin_user)
    client_request.post(
        "main.add_service",
        _data={
            "name": "testing the post",
            "organization_type": organization_type,
        },
        _expected_status=302,
        _expected_redirect=url_for(
            "main.service_dashboard",
            service_id=101,
        ),
    )
    assert mock_get_services.called


@pytest.mark.parametrize(
    ("name", "error_message"),
    [
        ("", "Cannot be empty"),
        (".", "Must include at least two alphanumeric characters"),
        ("a" * 256, "Service name must be 255 characters or fewer"),
    ],
)
def test_add_service_fails_if_service_name_fails_validation(
    client_request,
    mock_get_organization_by_domain,
    name,
    error_message,
    platform_admin_user,
):
    client_request.login(platform_admin_user)
    page = client_request.post(
        "main.add_service",
        _data={"name": name},
        _expected_status=200,
    )
    assert error_message in page.find("span", {"class": "usa-error-message"}).text


@freeze_time("2021-01-01")
def test_should_return_form_errors_with_duplicate_service_name_regardless_of_case(
    client_request, mock_get_organization_by_domain, mocker, platform_admin_user
):
    def _create(**_kwargs):
        json_mock = mocker.Mock(
            return_value={"message": {"name": ["Duplicate service name"]}}
        )
        resp_mock = mocker.Mock(status_code=400, json=json_mock)
        http_error = HTTPError(response=resp_mock, message="Default message")
        raise http_error

    mocker.patch("app.service_api_client.create_service", side_effect=_create)
    client_request.login(platform_admin_user)
    page = client_request.post(
        "main.add_service",
        _data={
            "name": "SERVICE ONE",
            "organization_type": "federal",
        },
        _expected_status=200,
    )
    assert (
        "This service name is already in use"
        in page.select_one(".usa-error-message").text.strip()
    )


def test_non_government_user_cannot_access_create_service_page(
    client_request,
    mock_get_non_govuser,
    api_nongov_user_active,
    mock_get_organizations,
):
    assert is_gov_user(api_nongov_user_active["email_address"]) is False
    client_request.login(api_nongov_user_active)
    client_request.get(
        "main.add_service",
        _expected_status=403,
    )


def test_non_government_user_cannot_create_service(
    client_request,
    mock_get_non_govuser,
    api_nongov_user_active,
    mock_get_organizations,
):
    assert is_gov_user(api_nongov_user_active["email_address"]) is False
    client_request.login(api_nongov_user_active)
    client_request.post(
        "main.add_service",
        _data={"name": "SERVICE TWO"},
        _expected_status=403,
    )
