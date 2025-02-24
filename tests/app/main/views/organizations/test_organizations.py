import pytest
from flask import url_for
from freezegun import freeze_time
from notifications_python_client.errors import HTTPError

from tests import organization_json, service_json
from tests.conftest import (
    ORGANISATION_ID,
    SERVICE_ONE_ID,
    SERVICE_TWO_ID,
    create_active_user_with_permissions,
    create_platform_admin_user,
    normalize_spaces,
)


def test_organization_page_shows_all_organizations(
    client_request, platform_admin_user, mocker
):
    orgs = [
        {"id": "A3", "name": "Test 3", "active": True, "count_of_live_services": 0},
        {"id": "B1", "name": "Test 1", "active": True, "count_of_live_services": 1},
        {"id": "C2", "name": "Test 2", "active": False, "count_of_live_services": 2},
    ]

    get_organizations = mocker.patch(
        "app.models.organization.AllOrganizations.client_method", return_value=orgs
    )
    client_request.login(platform_admin_user)
    page = client_request.get(".organizations")

    assert normalize_spaces(page.select_one("h1").text) == "Organizations"

    assert [
        (
            normalize_spaces(link.text),
            normalize_spaces(hint.text),
            link["href"],
        )
        for link, hint in zip(
            page.select(".browse-list-item a"),
            page.select(".browse-list-item .browse-list-hint"),
        )
    ] == [
        (
            "Test 1",
            "1 live service",
            url_for("main.organization_dashboard", org_id="B1"),
        ),
        (
            "Test 2",
            "2 live services",
            url_for("main.organization_dashboard", org_id="C2"),
        ),
        (
            "Test 3",
            "0 live services",
            url_for("main.organization_dashboard", org_id="A3"),
        ),
    ]

    archived = page.select_one(".table-field-status-default.heading-medium")
    assert normalize_spaces(archived.text) == "- archived"
    assert normalize_spaces(archived.parent.text) == "Test 2 - archived 2 live services"

    assert (
        normalize_spaces(page.select_one("a.govuk-button--secondary").text)
        == "New organization"
    )
    get_organizations.assert_called_once_with()


def test_view_organization_shows_the_correct_organization(client_request, mocker):
    org = {"id": ORGANISATION_ID, "name": "Test 1", "active": True}
    mocker.patch("app.organizations_client.get_organization", return_value=org)
    mocker.patch(
        "app.organizations_client.get_services_and_usage", return_value={"services": {}}
    )

    page = client_request.get(
        ".organization_dashboard",
        org_id=ORGANISATION_ID,
    )

    assert normalize_spaces(page.select_one("h1").text) == "Usage"
    assert normalize_spaces(page.select_one(".usa-hint").text) == (
        "Test 1 has no live services on Notify.gov"
    )
    assert not page.select("a[download]")


def test_page_to_create_new_organization(
    client_request,
    platform_admin_user,
    mocker,
):
    client_request.login(platform_admin_user)
    page = client_request.get(".add_organization")

    assert [
        (input["type"], input["name"], input.get("value"))
        for input in page.select("input")
    ] == [
        ("text", "name", None),
        ("radio", "organization_type", "federal"),
        ("radio", "organization_type", "state"),
        # ('radio', 'organization_type', 'nhs_central'),
        # ('radio', 'organization_type', 'nhs_local'),
        # ('radio', 'organization_type', 'nhs_gp'),
        # ('radio', 'organization_type', 'emergency_service'),
        # ('radio', 'organization_type', 'school_or_college'),
        ("radio", "organization_type", "other"),
        ("hidden", "csrf_token", mocker.ANY),
    ]


def test_create_new_organization(
    client_request,
    platform_admin_user,
    mocker,
):
    mock_create_organization = mocker.patch(
        "app.organizations_client.create_organization",
        return_value=organization_json(ORGANISATION_ID),
    )

    client_request.login(platform_admin_user)
    client_request.post(
        ".add_organization",
        _data={
            "name": "new name",
            "organization_type": "federal",
        },
        _expected_redirect=url_for(
            "main.organization_settings",
            org_id=ORGANISATION_ID,
        ),
    )

    mock_create_organization.assert_called_once_with(
        name="new name",
        organization_type="federal",
    )


def test_create_new_organization_validates(
    client_request,
    platform_admin_user,
    mocker,
):
    mock_create_organization = mocker.patch(
        "app.organizations_client.create_organization"
    )

    client_request.login(platform_admin_user)
    page = client_request.post(
        ".add_organization",
        _expected_status=200,
    )
    assert [
        (error["data-error-label"], normalize_spaces(error.text))
        for error in page.select(".usa-error-message")
    ] == [
        ("name", "Error: Cannot be empty"),
        ("organization_type", "Error: Select the type of organization"),
    ]
    assert mock_create_organization.called is False


@pytest.mark.parametrize(
    ("name", "error_message"),
    [
        ("", "Cannot be empty"),
        ("a", "at least two alphanumeric characters"),
        ("a" * 256, "Organization name must be 255 characters or fewer"),
    ],
)
def test_create_new_organization_fails_with_incorrect_input(
    client_request,
    platform_admin_user,
    mocker,
    name,
    error_message,
):
    mock_create_organization = mocker.patch(
        "app.organizations_client.create_organization"
    )

    client_request.login(platform_admin_user)
    page = client_request.post(
        ".add_organization",
        _data={
            "name": name,
            "organization_type": "local",
        },
        _expected_status=200,
    )
    assert mock_create_organization.called is False
    assert error_message in page.select_one(".usa-error-message").text


def test_create_new_organization_fails_with_duplicate_name(
    client_request,
    platform_admin_user,
    mocker,
):
    def _create(**_kwargs):
        json_mock = mocker.Mock(
            return_value={"message": "Organization name already exists"}
        )
        resp_mock = mocker.Mock(status_code=400, json=json_mock)
        http_error = HTTPError(response=resp_mock, message="Default message")
        raise http_error

    mocker.patch("app.organizations_client.create_organization", side_effect=_create)

    client_request.login(platform_admin_user)
    page = client_request.post(
        ".add_organization",
        _data={
            "name": "Existing org",
            "organization_type": "federal",
        },
        _expected_status=200,
    )

    error_message = "This organization name is already in use"
    assert error_message in page.select_one(".usa-error-message").text


@pytest.mark.parametrize(
    ("organization_type", "organization", "expected_status"),
    [
        ("nhs_gp", None, 200),
        ("central", None, 403),
        ("nhs_gp", organization_json(organization_type="nhs_gp"), 403),
    ],
)
@pytest.mark.skip(reason="Update for TTS")
def test_gps_can_create_own_organizations(
    client_request,
    mocker,
    mock_get_service_organization,
    service_one,
    organization_type,
    organization,
    expected_status,
):
    mocker.patch("app.organizations_client.get_organization", return_value=organization)
    service_one["organization_type"] = organization_type

    page = client_request.get(
        ".add_organization_from_gp_service",
        service_id=SERVICE_ONE_ID,
        _expected_status=expected_status,
    )

    if expected_status == 403:
        return

    assert page.select_one("input[type=text]")["name"] == "name"
    assert normalize_spaces(page.select_one("label[for=name]").text) == (
        "What’s your practice called?"
    )


@pytest.mark.parametrize(
    ("data", "expected_service_name"),
    [
        (
            {
                "same_as_service_name": False,
                "name": "Dr. Example",
            },
            "Dr. Example",
        ),
        (
            {
                "same_as_service_name": True,
                "name": "This is ignored",
            },
            "service one",
        ),
    ],
)
@pytest.mark.skip(reason="Update for TTS")
def test_gps_can_name_their_organization(
    client_request,
    mocker,
    service_one,
    mock_update_service_organization,
    data,
    expected_service_name,
):
    service_one["organization_type"] = "nhs_gp"
    mock_create_organization = mocker.patch(
        "app.organizations_client.create_organization",
        return_value=organization_json(ORGANISATION_ID),
    )

    client_request.post(
        ".add_organization_from_gp_service",
        service_id=SERVICE_ONE_ID,
        _data=data,
        _expected_status=302,
    )

    mock_create_organization.assert_called_once_with(
        name=expected_service_name,
        organization_type="nhs_gp",
    )
    mock_update_service_organization.assert_called_once_with(
        SERVICE_ONE_ID, ORGANISATION_ID
    )


@pytest.mark.parametrize(
    ("data", "expected_error"),
    [
        (
            {
                "name": "Dr. Example",
            },
            "Select yes or no",
        ),
        (
            {
                "same_as_service_name": False,
                "name": "",
            },
            "Cannot be empty",
        ),
    ],
)
@pytest.mark.skip(reason="Update for TTS")
def test_validation_of_gps_creating_organizations(
    client_request,
    mocker,
    service_one,
    data,
    expected_error,
):
    service_one["organization_type"] = "nhs_gp"
    page = client_request.post(
        ".add_organization_from_gp_service",
        service_id=SERVICE_ONE_ID,
        _data=data,
        _expected_status=200,
    )
    assert expected_error in page.select_one(".usa-error-message, .error-message").text


@freeze_time("2020-02-20 20:20")
def test_organization_services_shows_live_services_and_usage(
    client_request,
    mock_get_organization,
    mocker,
    active_user_with_permissions,
    fake_uuid,
):
    mock = mocker.patch(
        "app.organizations_client.get_services_and_usage",
        return_value={
            "services": [
                {
                    "service_id": SERVICE_ONE_ID,
                    "service_name": "1",
                    "chargeable_billable_sms": 250122,
                    "emails_sent": 13000,
                    "free_sms_limit": 250000,
                    "sms_billable_units": 122,
                    "sms_cost": 0,
                    "sms_remainder": None,
                },
                {
                    "service_id": SERVICE_TWO_ID,
                    "service_name": "5",
                    "chargeable_billable_sms": 0,
                    "emails_sent": 20000,
                    "free_sms_limit": 250000,
                    "sms_billable_units": 2500,
                    "sms_cost": 42.0,
                    "sms_remainder": None,
                },
            ]
        },
    )

    client_request.login(active_user_with_permissions)
    page = client_request.get(".organization_dashboard", org_id=ORGANISATION_ID)
    mock.assert_called_once_with(ORGANISATION_ID, 2020)

    services = page.select("main h3")
    usage_rows = page.select("main .grid-col-6")
    assert len(services) == 2

    # Totals
    assert normalize_spaces(usage_rows[0].text) == "Emails 33,000 sent"
    assert normalize_spaces(usage_rows[1].text) == "Text messages $42.00 spent"

    assert normalize_spaces(services[0].text) == "1"
    assert normalize_spaces(services[1].text) == "5"
    assert services[0].find("a")["href"] == url_for(
        "main.usage", service_id=SERVICE_ONE_ID
    )

    assert normalize_spaces(usage_rows[2].text) == "13,000 emails sent"
    assert normalize_spaces(usage_rows[3].text) == "122 free text messages sent"
    assert services[1].find("a")["href"] == url_for(
        "main.usage", service_id=SERVICE_TWO_ID
    )
    assert normalize_spaces(usage_rows[4].text) == "20,000 emails sent"
    assert normalize_spaces(usage_rows[5].text) == "$42.00 spent on text messages"

    # Ensure there’s no ‘this org has no services message’
    assert not page.select(".usa-hint")


@freeze_time("2020-02-20 20:20")
def test_organization_services_shows_live_services_and_usage_with_count_of_1(
    client_request,
    mock_get_organization,
    mocker,
    active_user_with_permissions,
    fake_uuid,
):
    mocker.patch(
        "app.organizations_client.get_services_and_usage",
        return_value={
            "services": [
                {
                    "service_id": SERVICE_ONE_ID,
                    "service_name": "1",
                    "chargeable_billable_sms": 1,
                    "emails_sent": 1,
                    "free_sms_limit": 250000,
                    "sms_billable_units": 1,
                    "sms_cost": 0,
                    "sms_remainder": None,
                },
            ]
        },
    )

    client_request.login(active_user_with_permissions)
    page = client_request.get(".organization_dashboard", org_id=ORGANISATION_ID)

    usage_rows = page.select("main .grid-col-6")

    # Totals
    assert normalize_spaces(usage_rows[0].text) == "Emails 1 sent"
    assert normalize_spaces(usage_rows[1].text) == "Text messages $0.00 spent"

    assert normalize_spaces(usage_rows[2].text) == "1 email sent"
    assert normalize_spaces(usage_rows[3].text) == "1 free text message sent"


@freeze_time("2020-02-20 20:20")
@pytest.mark.parametrize(
    ("financial_year", "expected_selected"),
    [
        (2018, "2018 to 2019 fiscal year"),
        (2019, "2019 to 2020 fiscal year"),
        (2020, "2020 to 2021 fiscal year"),
    ],
)
def test_organization_services_filters_by_financial_year(
    client_request,
    mock_get_organization,
    mocker,
    active_user_with_permissions,
    fake_uuid,
    financial_year,
    expected_selected,
):
    mock = mocker.patch(
        "app.organizations_client.get_services_and_usage", return_value={"services": []}
    )
    page = client_request.get(
        ".organization_dashboard",
        org_id=ORGANISATION_ID,
        year=financial_year,
    )
    mock.assert_called_once_with(ORGANISATION_ID, financial_year)
    assert normalize_spaces(page.select_one(".pill").text) == (
        "2020 to 2021 fiscal year "
        "2019 to 2020 fiscal year "
        "2018 to 2019 fiscal year"
    )
    assert normalize_spaces(page.select_one(".pill-item--selected").text) == (
        expected_selected
    )


@freeze_time("2020-02-20 20:20")
def test_organization_services_shows_search_bar(
    client_request,
    mock_get_organization,
    mocker,
    active_user_with_permissions,
    fake_uuid,
):
    mocker.patch(
        "app.organizations_client.get_services_and_usage",
        return_value={
            "services": [
                {
                    "service_id": SERVICE_ONE_ID,
                    "service_name": "Service 1",
                    "chargeable_billable_sms": 250122,
                    "emails_sent": 13000,
                    "free_sms_limit": 250000,
                    "sms_billable_units": 122,
                    "sms_cost": 1.93,
                    "sms_remainder": None,
                },
            ]
            * 8
        },
    )

    client_request.login(active_user_with_permissions)
    page = client_request.get(".organization_dashboard", org_id=ORGANISATION_ID)

    services = page.select(".organization-service")
    assert len(services) == 8

    assert page.select_one(".live-search")["data-targets"] == ".organization-service"
    assert [
        normalize_spaces(service_name.text)
        for service_name in page.select(".live-search-relevant")
    ] == [
        "Service 1",
        "Service 1",
        "Service 1",
        "Service 1",
        "Service 1",
        "Service 1",
        "Service 1",
        "Service 1",
    ]


@freeze_time("2020-02-20 20:20")
def test_organization_services_hides_search_bar_for_7_or_fewer_services(
    client_request,
    mock_get_organization,
    mocker,
    active_user_with_permissions,
    fake_uuid,
):
    mocker.patch(
        "app.organizations_client.get_services_and_usage",
        return_value={
            "services": [
                {
                    "service_id": SERVICE_ONE_ID,
                    "service_name": "Service 1",
                    "chargeable_billable_sms": 250122,
                    "emails_sent": 13000,
                    "free_sms_limit": 250000,
                    "sms_billable_units": 122,
                    "sms_cost": 1.93,
                    "sms_remainder": None,
                },
            ]
            * 7
        },
    )

    client_request.login(active_user_with_permissions)
    page = client_request.get(".organization_dashboard", org_id=ORGANISATION_ID)

    services = page.select(".organization-service")
    assert len(services) == 7
    assert not page.select_one(".live-search")


@freeze_time("2021-11-12 11:09:00.061258")
def test_organization_services_links_to_downloadable_report(
    client_request,
    mock_get_organization,
    mocker,
    active_user_with_permissions,
    fake_uuid,
):
    mocker.patch(
        "app.organizations_client.get_services_and_usage",
        return_value={
            "services": [
                {
                    "service_id": SERVICE_ONE_ID,
                    "service_name": "Service 1",
                    "chargeable_billable_sms": 250122,
                    "emails_sent": 13000,
                    "free_sms_limit": 250000,
                    "sms_billable_units": 122,
                    "sms_cost": 1.93,
                    "sms_remainder": None,
                },
            ]
            * 2
        },
    )
    client_request.login(active_user_with_permissions)
    page = client_request.get(".organization_dashboard", org_id=ORGANISATION_ID)

    link_to_report = page.select_one("a[download]")
    assert normalize_spaces(link_to_report.text) == "Download this report (CSV)"
    assert link_to_report.attrs["href"] == url_for(
        ".download_organization_usage_report",
        org_id=ORGANISATION_ID,
        selected_year=2021,
    )


@freeze_time("2021-11-12 11:09:00.061258")
def test_download_organization_usage_report(
    client_request,
    mock_get_organization,
    mocker,
    active_user_with_permissions,
    fake_uuid,
):
    mocker.patch(
        "app.organizations_client.get_services_and_usage",
        return_value={
            "services": [
                {
                    "service_id": SERVICE_ONE_ID,
                    "service_name": "Service 1",
                    "chargeable_billable_sms": 22,
                    "emails_sent": 13000,
                    "free_sms_limit": 100,
                    "sms_billable_units": 122,
                    "sms_cost": 1.934,
                    "sms_remainder": 0,
                },
                {
                    "service_id": SERVICE_TWO_ID,
                    "service_name": "Service 1",
                    "chargeable_billable_sms": 222,
                    "emails_sent": 23000,
                    "free_sms_limit": 250000,
                    "sms_billable_units": 322,
                    "sms_cost": 3.935,
                    "sms_remainder": 0,
                },
            ]
        },
    )
    client_request.login(active_user_with_permissions)
    csv_report = client_request.get(
        ".download_organization_usage_report",
        org_id=ORGANISATION_ID,
        selected_year=2021,
        _test_page_title=False,
    )

    assert csv_report.string == (
        "Service ID,Service Name,Emails sent,Free text message allowance remaining,"
        "Spent on text messages ($)"
        "\r\n596364a0-858e-42c8-9062-a8fe822260eb,Service 1,13000,0,1.93"
        "\r\n147ad62a-2951-4fa1-9ca0-093cd1a52c52,Service 1,23000,0,3.94\r\n"
    )


def test_organization_trial_mode_services_shows_all_non_live_services(
    client_request,
    platform_admin_user,
    mock_get_organization,
    mocker,
    fake_uuid,
):
    mocker.patch(
        "app.organizations_client.get_organization_services",
        return_value=[
            service_json(id_="1", name="1", restricted=False, active=True),  # live
            service_json(id_="2", name="2", restricted=True, active=True),  # trial
            service_json(id_="3", name="3", restricted=False, active=False),  # archived
        ],
    )

    client_request.login(platform_admin_user)
    page = client_request.get(
        ".organization_trial_mode_services",
        org_id=ORGANISATION_ID,
        _test_page_title=False,
    )

    services = page.select(".browse-list-item")
    assert len(services) == 2

    assert normalize_spaces(services[0].text) == "2"
    assert normalize_spaces(services[1].text) == "3"
    assert services[0].find("a")["href"] == url_for(
        "main.service_dashboard", service_id="2"
    )
    assert services[1].find("a")["href"] == url_for(
        "main.service_dashboard", service_id="3"
    )


def test_organization_trial_mode_services_doesnt_work_if_not_platform_admin(
    client_request,
    mock_get_organization,
):
    client_request.get(
        ".organization_trial_mode_services",
        org_id=ORGANISATION_ID,
        _expected_status=403,
    )


def test_manage_org_users_shows_correct_link_next_to_each_user(
    client_request,
    mock_get_organization,
    mock_get_users_for_organization,
    mock_get_invited_users_for_organization,
):
    page = client_request.get(
        ".manage_org_users",
        org_id=ORGANISATION_ID,
    )

    # No banner confirming a user to be deleted shown
    assert not page.select_one(".banner-dangerous")

    users = page.find_all(class_="user-list-item")

    # The first user is an invited user, so has the link to cancel the invitation.
    # The second two users are active users, so have the link to be removed from the org
    assert (
        normalize_spaces(users[0].text)
        == "invited_user@test.gsa.gov (invited) Cancel invitation for invited_user@test.gsa.gov"
    )
    assert (
        normalize_spaces(users[1].text)
        == "Test User 1 test@gsa.gov Remove Test User 1 test@gsa.gov"
    )
    assert (
        normalize_spaces(users[2].text)
        == "Test User 2 testt@gsa.gov Remove Test User 2 testt@gsa.gov"
    )

    assert users[0].a["href"] == url_for(
        ".cancel_invited_org_user",
        org_id=ORGANISATION_ID,
        invited_user_id="73616d70-6c65-4f6f-b267-5f696e766974",
    )
    assert users[1].a["href"] == url_for(
        ".edit_organization_user", org_id=ORGANISATION_ID, user_id="1234"
    )
    assert users[2].a["href"] == url_for(
        ".edit_organization_user", org_id=ORGANISATION_ID, user_id="5678"
    )


def test_manage_org_users_shows_no_link_for_cancelled_users(
    client_request,
    mock_get_organization,
    mock_get_users_for_organization,
    sample_org_invite,
    mocker,
):
    sample_org_invite["status"] = "cancelled"
    mocker.patch(
        "app.models.user.OrganizationInvitedUsers.client_method",
        return_value=[sample_org_invite],
    )

    page = client_request.get(
        ".manage_org_users",
        org_id=ORGANISATION_ID,
    )
    users = page.find_all(class_="user-list-item")

    assert (
        normalize_spaces(users[0].text)
        == "invited_user@test.gsa.gov (cancelled invite)"
    )
    assert not users[0].a


@pytest.mark.parametrize(
    "number_of_users",
    [
        pytest.param(8),
        pytest.param(800),
    ],
)
def test_manage_org_users_should_show_live_search_if_more_than_7_users(
    client_request,
    mocker,
    mock_get_organization,
    active_user_with_permissions,
    number_of_users,
):
    mocker.patch(
        "app.models.user.OrganizationInvitedUsers.client_method",
        return_value=[],
    )
    mocker.patch(
        "app.models.user.OrganizationUsers.client_method",
        return_value=[active_user_with_permissions] * number_of_users,
    )

    page = client_request.get(
        ".manage_org_users",
        org_id=ORGANISATION_ID,
    )

    assert page.select_one("div[data-module=live-search]")["data-targets"] == (
        ".user-list-item"
    )
    assert len(page.select(".user-list-item")) == number_of_users

    textbox = page.select_one("[data-module=autofocus] .usa-input")
    assert "value" not in textbox
    assert textbox["name"] == "search"
    # data-module=autofocus is set on a containing element so it
    # shouldn’t also be set on the textbox itself
    assert "data-module" not in textbox
    assert not page.select_one("[data-force-focus]")
    assert textbox["class"] == ["usa-input"]
    assert (
        normalize_spaces(page.select_one("label[class=usa-label]").text)
        == "Search by name or email address"
    )


@pytest.mark.parametrize(
    "number_of_users",
    [
        pytest.param(3),
        pytest.param(7),
    ],
)
def test_manage_org_users_should_show_live_search_if_7_users_or_less(
    client_request,
    mocker,
    mock_get_organization,
    active_user_with_permissions,
    number_of_users,
):
    mocker.patch(
        "app.models.user.OrganizationInvitedUsers.client_method",
        return_value=[],
    )
    mocker.patch(
        "app.models.user.OrganizationUsers.client_method",
        return_value=[active_user_with_permissions] * number_of_users,
    )

    page = client_request.get(
        ".manage_org_users",
        org_id=ORGANISATION_ID,
    )

    with pytest.raises(expected_exception=TypeError):
        assert page.select_one("div[data-module=live-search]")["data-targets"] == (
            ".user-list-item"
        )


def test_edit_organization_user_shows_the_delete_confirmation_banner(
    client_request,
    mock_get_organization,
    mock_get_invites_for_organization,
    mock_get_users_for_organization,
    active_user_with_permissions,
):
    page = client_request.get(
        ".edit_organization_user",
        org_id=ORGANISATION_ID,
        user_id=active_user_with_permissions["id"],
    )

    assert normalize_spaces(page.h1) == "Team members"

    banner = page.select_one(".banner-dangerous")
    assert "Are you sure you want to remove Test User?" in normalize_spaces(
        banner.contents[0]
    )
    assert banner.form.attrs["action"] == url_for(
        "main.remove_user_from_organization",
        org_id=ORGANISATION_ID,
        user_id=active_user_with_permissions["id"],
    )


def test_remove_user_from_organization_makes_api_request_to_remove_user(
    client_request,
    mocker,
    mock_get_organization,
    fake_uuid,
):
    mock_remove_user = mocker.patch(
        "app.organizations_client.remove_user_from_organization"
    )

    client_request.post(
        ".remove_user_from_organization",
        org_id=ORGANISATION_ID,
        user_id=fake_uuid,
        _expected_redirect=url_for(
            "main.show_accounts_or_dashboard",
        ),
    )

    mock_remove_user.assert_called_with(ORGANISATION_ID, fake_uuid)


def test_organization_settings_platform_admin_only(
    client_request, mock_get_organization, organization_one
):
    client_request.get(
        ".organization_settings",
        org_id=organization_one["id"],
        _expected_status=403,
    )


def test_organization_settings_for_platform_admin(
    client_request, platform_admin_user, mock_get_organization, organization_one
):
    expected_rows = [
        "Label Value Action",
        "Name Test organization Change organization name",
        "Sector Federal government Change sector for the organization",
        "Billing details None Change billing details for the organization",
        "Notes None Change the notes for the organization",
        "Known email domains None Change known email domains for the organization",
    ]

    client_request.login(platform_admin_user)
    page = client_request.get(".organization_settings", org_id=organization_one["id"])

    assert page.find("h1").text == "Settings"
    rows = page.select("tr")
    assert len(rows) == len(expected_rows)
    for index, row in enumerate(expected_rows):
        assert row == " ".join(rows[index].text.split())
    mock_get_organization.assert_called_with(organization_one["id"])


@pytest.mark.parametrize(
    ("endpoint", "expected_options", "expected_selected"),
    [
        (
            ".edit_organization_type",
            (
                {"value": "federal", "label": "Federal government"},
                {"value": "state", "label": "State government"},
                {"value": "other", "label": "Other"},
            ),
            "federal",
        ),
    ],
)
@pytest.mark.parametrize(
    "user",
    [
        pytest.param(
            create_platform_admin_user(),
        ),
        pytest.param(create_active_user_with_permissions(), marks=pytest.mark.xfail),
    ],
)
def test_view_organization_settings(
    client_request,
    fake_uuid,
    organization_one,
    mock_get_organization,
    endpoint,
    expected_options,
    expected_selected,
    user,
):
    client_request.login(user)

    page = client_request.get(endpoint, org_id=organization_one["id"])

    radios = page.select("input[type=radio]")

    for index, option in enumerate(expected_options):
        option_values = {
            "value": radios[index]["value"],
            "label": normalize_spaces(
                page.select_one("label[for={}]".format(radios[index]["id"])).text
            ),
        }
        if "hint" in option:
            option_values["hint"] = normalize_spaces(
                page.select_one(
                    "label[for={}] + .usa-hint".format(radios[index]["id"])
                ).text
            )
        assert option_values == option

    if expected_selected:
        assert page.select_one("input[checked]")["value"] == expected_selected
    else:
        assert not page.select_one("input[checked]")


@pytest.mark.parametrize(
    ("endpoint", "post_data", "expected_persisted"),
    [
        (
            ".edit_organization_type",
            {"organization_type": "federal"},
            {"cached_service_ids": [], "organization_type": "federal"},
        ),
        (
            ".edit_organization_type",
            {"organization_type": "state"},
            {"cached_service_ids": [], "organization_type": "state"},
        ),
    ],
)
@pytest.mark.parametrize(
    "user",
    [
        pytest.param(
            create_platform_admin_user(),
        ),
        pytest.param(
            create_active_user_with_permissions(),
        ),
    ],
)
def test_update_organization_settings(
    mocker,
    client_request,
    fake_uuid,
    organization_one,
    mock_get_organization,
    mock_update_organization,
    endpoint,
    post_data,
    expected_persisted,
    user,
):
    mocker.patch("app.organizations_client.get_organization_services", return_value=[])
    client_request.login(user)

    if user["email_address"] == "platform@admin.gsa.gov":
        expected_status = 302
        expected_redirect = url_for(
            "main.organization_settings",
            org_id=organization_one["id"],
        )
    else:
        expected_status = 403
        expected_redirect = None
    client_request.post(
        endpoint,
        org_id=organization_one["id"],
        _data=post_data,
        _expected_status=expected_status,
        _expected_redirect=expected_redirect,
    )

    if user["email_address"] == "platform@admin.gsa.gov":
        mock_update_organization.assert_called_once_with(
            organization_one["id"],
            **expected_persisted,
        )


def test_update_organization_sector_sends_service_id_data_to_api_client(
    client_request,
    mock_get_organization,
    organization_one,
    mock_get_organization_services,
    mock_update_organization,
    platform_admin_user,
):
    client_request.login(platform_admin_user)

    client_request.post(
        "main.edit_organization_type",
        org_id=organization_one["id"],
        _data={"organization_type": "federal"},
        _expected_status=302,
        _expected_redirect=url_for(
            "main.organization_settings",
            org_id=organization_one["id"],
        ),
    )

    mock_update_organization.assert_called_once_with(
        organization_one["id"],
        cached_service_ids=["12345", "67890", SERVICE_ONE_ID],
        organization_type="federal",
    )


@pytest.mark.parametrize(
    "user",
    [
        pytest.param(
            create_platform_admin_user(),
        ),
        pytest.param(create_active_user_with_permissions(), marks=pytest.mark.xfail),
    ],
)
def test_view_organization_domains(
    mocker,
    client_request,
    fake_uuid,
    user,
):
    client_request.login(user)

    mocker.patch(
        "app.organizations_client.get_organization",
        side_effect=lambda org_id: organization_json(
            org_id,
            "Org 1",
            domains=["example.gsa.gov", "test.example.gsa.gov"],
        ),
    )

    page = client_request.get(
        "main.edit_organization_domains",
        org_id=ORGANISATION_ID,
    )

    assert [textbox.get("value") for textbox in page.select("input[type=text]")] == [
        "example.gsa.gov",
        "test.example.gsa.gov",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ]


@pytest.mark.parametrize(
    ("post_data", "expected_persisted"),
    [
        (
            {
                "domains-0": "example.gsa.gov",
                "domains-2": "example.gsa.gov",
                "domains-3": "EXAMPLE.gsa.gov",
                "domains-5": "test.gsa.gov",
            },
            {
                "domains": [
                    "example.gsa.gov",
                    "test.gsa.gov",
                ]
            },
        ),
        (
            {
                "domains-0": "",
                "domains-1": "",
                "domains-2": "",
            },
            {"domains": []},
        ),
    ],
)
@pytest.mark.parametrize(
    "user",
    [
        pytest.param(
            create_platform_admin_user(),
        ),
        pytest.param(
            create_active_user_with_permissions(),
        ),
    ],
)
def test_update_organization_domains(
    client_request,
    fake_uuid,
    organization_one,
    mock_get_organization,
    mock_update_organization,
    post_data,
    expected_persisted,
    user,
):
    client_request.login(user)
    if user["email_address"] == "platform@admin.gsa.gov":
        expected_status = 302
        expected_redirect = url_for(
            "main.organization_settings",
            org_id=organization_one["id"],
        )
    else:
        expected_status = 403
        expected_redirect = None

    client_request.post(
        "main.edit_organization_domains",
        org_id=ORGANISATION_ID,
        _data=post_data,
        _expected_status=expected_status,
        _expected_redirect=expected_redirect,
    )

    if user["email_address"] == "platform@admin.gsa.gov":
        mock_update_organization.assert_called_once_with(
            ORGANISATION_ID,
            **expected_persisted,
        )


def test_update_organization_domains_when_domain_already_exists(
    mocker,
    client_request,
    fake_uuid,
    organization_one,
    mock_get_organization,
):
    user = create_platform_admin_user()
    client_request.login(user)

    mocker.patch(
        "app.organizations_client.update_organization",
        side_effect=HTTPError(
            response=mocker.Mock(
                status_code=400,
                json={"result": "error", "message": "Domain already exists"},
            ),
            message="Domain already exists",
        ),
    )

    response = client_request.post(
        "main.edit_organization_domains",
        org_id=ORGANISATION_ID,
        _data={
            "domains": [
                "example.gsa.gov",
            ]
        },
        _expected_status=200,
    )

    assert (
        response.find("div", class_="banner-dangerous").text.strip()
        == "This domain is already in use"
    )


def test_update_organization_name(
    client_request,
    platform_admin_user,
    fake_uuid,
    mock_get_organization,
    mock_update_organization,
):
    client_request.login(platform_admin_user)
    client_request.post(
        ".edit_organization_name",
        org_id=fake_uuid,
        _data={"name": "TestNewOrgName"},
        _expected_redirect=url_for(
            ".organization_settings",
            org_id=fake_uuid,
        ),
    )
    mock_update_organization.assert_called_once_with(
        fake_uuid,
        name="TestNewOrgName",
        cached_service_ids=None,
    )


@pytest.mark.parametrize(
    ("name", "error_message"),
    [
        ("", "Cannot be empty"),
        ("a", "at least two alphanumeric characters"),
        ("a" * 256, "Organization name must be 255 characters or fewer"),
    ],
)
def test_update_organization_with_incorrect_input(
    client_request,
    platform_admin_user,
    organization_one,
    mock_get_organization,
    name,
    error_message,
):
    client_request.login(platform_admin_user)
    page = client_request.post(
        ".edit_organization_name",
        org_id=organization_one["id"],
        _data={"name": name},
        _expected_status=200,
    )
    assert error_message in page.select_one(".usa-error-message").text


def test_update_organization_with_non_unique_name(
    client_request,
    platform_admin_user,
    fake_uuid,
    mock_get_organization,
    mocker,
):
    mocker.patch(
        "app.organizations_client.update_organization",
        side_effect=HTTPError(
            response=mocker.Mock(
                status_code=400,
                json={"result": "error", "message": "Organization name already exists"},
            ),
            message="Organization name already exists",
        ),
    )
    client_request.login(platform_admin_user)
    page = client_request.post(
        ".edit_organization_name",
        org_id=fake_uuid,
        _data={"name": "TestNewOrgName"},
        _expected_status=200,
    )

    assert (
        "This organization name is already in use"
        in page.select_one(".usa-error-message").text
    )


def test_organization_settings_links_to_edit_organization_notes_page(
    mocker,
    mock_get_organization,
    organization_one,
    client_request,
    platform_admin_user,
):
    client_request.login(platform_admin_user)
    page = client_request.get(".organization_settings", org_id=organization_one["id"])
    assert (
        len(
            page.find_all(
                "a",
                attrs={
                    "href": "/organizations/{}/settings/notes".format(
                        organization_one["id"]
                    )
                },
            )
        )
        == 1
    )


def test_view_edit_organization_notes(
    client_request,
    platform_admin_user,
    organization_one,
    mock_get_organization,
):
    client_request.login(platform_admin_user)
    page = client_request.get(
        "main.edit_organization_notes",
        org_id=organization_one["id"],
    )
    assert page.select_one("h1").text == "Edit organization notes"
    assert page.find("label", class_="usa-label").text.strip() == "Notes"
    assert page.find("textarea").attrs["name"] == "notes"


def test_update_organization_notes(
    client_request,
    platform_admin_user,
    organization_one,
    mock_get_organization,
    mock_update_organization,
):
    client_request.login(platform_admin_user)
    client_request.post(
        "main.edit_organization_notes",
        org_id=organization_one["id"],
        _data={"notes": "Very fluffy"},
        _expected_redirect=url_for(
            "main.organization_settings",
            org_id=organization_one["id"],
        ),
    )
    mock_update_organization.assert_called_with(
        organization_one["id"], cached_service_ids=None, notes="Very fluffy"
    )


def test_update_organization_notes_errors_when_user_not_platform_admin(
    client_request,
    organization_one,
    mock_get_organization,
    mock_update_organization,
):
    client_request.post(
        "main.edit_organization_notes",
        org_id=organization_one["id"],
        _data={"notes": "Very fluffy"},
        _expected_status=403,
    )


def test_update_organization_notes_doesnt_call_api_when_notes_dont_change(
    client_request,
    platform_admin_user,
    organization_one,
    mock_update_organization,
    mocker,
):
    mocker.patch(
        "app.organizations_client.get_organization",
        return_value=organization_json(
            id_=organization_one["id"], name="Test Org", notes="Very fluffy"
        ),
    )
    client_request.login(platform_admin_user)
    client_request.post(
        "main.edit_organization_notes",
        org_id=organization_one["id"],
        _data={"notes": "Very fluffy"},
        _expected_redirect=url_for(
            "main.organization_settings",
            org_id=organization_one["id"],
        ),
    )
    assert not mock_update_organization.called


def test_organization_settings_links_to_edit_organization_billing_details_page(
    mocker,
    mock_get_organization,
    organization_one,
    client_request,
    platform_admin_user,
):
    client_request.login(platform_admin_user)
    page = client_request.get(".organization_settings", org_id=organization_one["id"])
    assert (
        len(
            page.find_all(
                "a",
                attrs={
                    "href": "/organizations/{}/settings/edit-billing-details".format(
                        organization_one["id"]
                    )
                },
            )
        )
        == 1
    )


def test_view_edit_organization_billing_details(
    client_request,
    platform_admin_user,
    organization_one,
    mock_get_organization,
):
    client_request.login(platform_admin_user)
    page = client_request.get(
        "main.edit_organization_billing_details",
        org_id=organization_one["id"],
    )
    assert page.select_one("h1").text == "Edit organization billing details"
    labels = page.find_all("label", class_="usa-label")
    labels_list = [
        "Contact email addresses",
        "Contact names",
        "Reference",
        "Purchase order number",
        "Notes",
    ]
    for label in labels:
        assert label.text.strip() in labels_list
    textbox_names = page.find_all("input", class_="usa-input ")
    names_list = [
        "billing_contact_email_addresses",
        "billing_contact_names",
        "billing_reference",
        "purchase_order_number",
    ]

    for name in textbox_names:
        assert name.attrs["name"] in names_list

    assert page.find("textarea").attrs["name"] == "notes"


def test_update_organization_billing_details(
    client_request,
    platform_admin_user,
    organization_one,
    mock_get_organization,
    mock_update_organization,
):
    client_request.login(platform_admin_user)
    client_request.post(
        "main.edit_organization_billing_details",
        org_id=organization_one["id"],
        _data={
            "billing_contact_email_addresses": "accounts@fluff.gsa.gov",
            "billing_contact_names": "Flannellette von Fluff",
            "billing_reference": "",
            "purchase_order_number": "PO1234",
            "notes": "very fluffy, give extra allowance",
        },
        _expected_redirect=url_for(
            "main.organization_settings",
            org_id=organization_one["id"],
        ),
    )
    mock_update_organization.assert_called_with(
        organization_one["id"],
        cached_service_ids=None,
        billing_contact_email_addresses="accounts@fluff.gsa.gov",
        billing_contact_names="Flannellette von Fluff",
        billing_reference="",
        purchase_order_number="PO1234",
        notes="very fluffy, give extra allowance",
    )


def test_update_organization_billing_details_errors_when_user_not_platform_admin(
    client_request,
    organization_one,
    mock_get_organization,
    mock_update_organization,
):
    client_request.post(
        "main.edit_organization_billing_details",
        org_id=organization_one["id"],
        _data={"notes": "Very fluffy"},
        _expected_status=403,
    )


def test_organization_billing_page_not_accessible_if_not_platform_admin(
    client_request,
    mock_get_organization,
):
    client_request.get(
        ".organization_billing", org_id=ORGANISATION_ID, _expected_status=403
    )
