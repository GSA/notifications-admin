import copy
import uuid

import pytest
from flask import url_for

import app
from app.enums import ServicePermission
from app.utils.user import is_gov_user
from tests.conftest import (
    ORGANISATION_ID,
    ORGANISATION_TWO_ID,
    SERVICE_ONE_ID,
    USER_ONE_ID,
    create_active_user_empty_permissions,
    create_active_user_manage_template_permissions,
    create_active_user_view_permissions,
    create_active_user_with_permissions,
    create_platform_admin_user,
    normalize_spaces,
    sample_uuid,
)


@pytest.mark.parametrize(
    ("user", "expected_self_text", "add_details"),
    [
        (
            create_active_user_with_permissions(),
            (
                "Test User test@user.gsa.gov (you) "
                "Permissions "
                "Can See dashboard "
                "Can Send messages "
                "Can Add and edit templates "
                "Can Manage settings, team and usage"
            ),
            True,
        ),
        (
            create_active_user_empty_permissions(),
            ("Test User With Empty Permissions test@user.gsa.gov (you) " "Permissions"),
            False,
        ),
        (
            create_active_user_view_permissions(),
            (
                "Test User With Permissions test@user.gsa.gov (you) "
                "Permissions "
                "Can See dashboard"
            ),
            False,
        ),
        (
            create_active_user_manage_template_permissions(),
            (
                "Test User With Permissions test@user.gsa.gov (you) "
                "Permissions "
                "Can See dashboard "
                "Can Add and edit templates"
            ),
            False,
        ),
    ],
)
def test_should_show_overview_page(
    client_request,
    mocker,
    mock_get_invites_for_service,
    mock_get_template_folders,
    mock_has_no_jobs,
    service_one,
    user,
    expected_self_text,
    active_user_view_permissions,
    add_details,
):
    current_user = user
    other_user = copy.deepcopy(active_user_view_permissions)
    other_user["email_address"] = "zzzzzzz@example.gsa.gov"
    other_user["name"] = "ZZZZZZZZ"
    other_user["id"] = "zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz"

    client_request.login(current_user)
    mock_get_users = mocker.patch(
        "app.models.user.Users.client_method",
        return_value=[
            current_user,
            other_user,
        ],
    )

    page = client_request.get("main.manage_users", service_id=SERVICE_ONE_ID)

    assert normalize_spaces(page.select_one("h1").text) == "Team members"
    assert (
        normalize_spaces(page.select(".user-list-item")[0].text) == expected_self_text
    )

    expected = "ZZZZZZZZ zzzzzzz@example.gsa.gov " "Permissions " "Can See dashboard"

    if add_details is True:
        expected = f"{expected} Change details for ZZZZZZZZ zzzzzzz@example.gsa.gov"
    assert normalize_spaces(page.select(".user-list-item")[6].text) == expected
    mock_get_users.assert_called_once_with(SERVICE_ONE_ID)


@pytest.mark.parametrize(
    "state",
    [
        "active",
        "pending",
    ],
)
def test_should_show_change_details_link(
    client_request,
    mocker,
    mock_get_invites_for_service,
    mock_get_template_folders,
    service_one,
    active_user_with_permissions,
    active_caseworking_user,
    state,
):
    current_user = active_user_with_permissions

    other_user = active_caseworking_user
    other_user["id"] = uuid.uuid4()
    other_user["email_address"] = "zzzzzzz@example.gsa.gov"
    other_user["state"] = state

    mocker.patch("app.user_api_client.get_user", return_value=current_user)
    mocker.patch(
        "app.models.user.Users.client_method",
        return_value=[
            current_user,
            other_user,
        ],
    )

    page = client_request.get("main.manage_users", service_id=SERVICE_ONE_ID)
    link = page.select(".user-list-item")[-1].select_one("a")

    assert normalize_spaces(link.text) == (
        "Change details for Test User zzzzzzz@example.gsa.gov"
    )
    assert link["href"] == url_for(
        ".edit_user_permissions",
        service_id=SERVICE_ONE_ID,
        user_id=other_user["id"],
    )


@pytest.mark.parametrize(
    "number_of_users",
    [
        pytest.param(7),
        pytest.param(8),
    ],
)
def test_should_show_live_search_if_more_than_7_users(
    client_request,
    mocker,
    mock_get_invites_for_service,
    mock_get_template_folders,
    mock_has_no_jobs,
    active_user_with_permissions,
    active_user_view_permissions,
    number_of_users,
):
    mocker.patch(
        "app.user_api_client.get_user", return_value=active_user_with_permissions
    )
    mocker.patch("app.models.user.InvitedUsers.client_method", return_value=[])
    mocker.patch(
        "app.models.user.Users.client_method",
        return_value=[active_user_with_permissions] * number_of_users,
    )

    page = client_request.get("main.manage_users", service_id=SERVICE_ONE_ID)

    if number_of_users == 7:
        with pytest.raises(expected_exception=TypeError):
            assert page.select_one("div[data-module=live-search]")["data-targets"] == (
                ".user-list-item"
            )
        return

    assert page.select_one("div[data-module=live-search]")["data-targets"] == (
        ".user-list-item"
    )
    assert len(page.select(".user-list-item")) == number_of_users

    textbox = page.select_one(".usa-input")
    assert "value" not in textbox
    assert textbox["name"] == "search"
    # data-module=autofocus is set on a containing element so it
    # shouldn’t also be set on the textbox itself
    assert "data-module" not in textbox
    assert not page.select_one("[data-force-focus]")
    assert textbox["class"] == [
        "usa-input",
    ]
    assert (
        normalize_spaces(page.select_one("label:contains('Search by')").text)
        == "Search by name or email address"
    )


def test_should_show_caseworker_on_overview_page(
    client_request,
    mocker,
    mock_get_invites_for_service,
    mock_get_template_folders,
    service_one,
    active_user_view_permissions,
    active_caseworking_user,
):
    service_one["permissions"].append("caseworking")
    current_user = active_user_view_permissions

    other_user = active_caseworking_user
    other_user["id"] = uuid.uuid4()
    other_user["email_address"] = "zzzzzzz@example.gsa.gov"

    client_request.login(current_user)
    mocker.patch(
        "app.models.user.Users.client_method",
        return_value=[
            current_user,
            other_user,
        ],
    )

    page = client_request.get("main.manage_users", service_id=SERVICE_ONE_ID)

    assert normalize_spaces(page.select_one("h1").text) == "Team members"
    assert normalize_spaces(page.select(".user-list-item")[0].text) == (
        "Test User With Permissions test@user.gsa.gov (you) "
        "Permissions "
        "Can See dashboard"
    )
    # [1:5] are invited users
    assert normalize_spaces(page.select(".user-list-item")[6].text) == (
        "Test User zzzzzzz@example.gsa.gov " "Permissions " "Can Send messages"
    )


@pytest.mark.parametrize(
    ("endpoint", "extra_args", "service_has_email_auth", "auth_options_hidden"),
    [
        ("main.edit_user_permissions", {"user_id": sample_uuid()}, True, False),
        ("main.edit_user_permissions", {"user_id": sample_uuid()}, False, True),
        ("main.invite_user", {}, True, False),
        ("main.invite_user", {}, False, True),
    ],
)
def test_service_with_no_email_auth_hides_auth_type_options(
    client_request,
    endpoint,
    extra_args,
    service_has_email_auth,
    auth_options_hidden,
    service_one,
    mock_get_users_by_service,
    mock_get_template_folders,
    platform_admin_user,
):
    if service_has_email_auth:
        service_one["permissions"].append(ServicePermission.EMAIL_AUTH)
    client_request.login(platform_admin_user)
    page = client_request.get(endpoint, service_id=service_one["id"], **extra_args)
    assert (
        page.find("input", attrs={"name": "login_authentication"}) is None
    ) == auth_options_hidden


@pytest.mark.parametrize("service_has_caseworking", [True, False])
@pytest.mark.parametrize(
    ("endpoint", "extra_args"),
    [
        (
            "main.edit_user_permissions",
            {"user_id": sample_uuid()},
        ),
        (
            "main.invite_user",
            {},
        ),
    ],
)
def test_service_without_caseworking_doesnt_show_admin_vs_caseworker(
    client_request,
    mock_get_users_by_service,
    mock_get_template_folders,
    endpoint,
    service_has_caseworking,
    extra_args,
    platform_admin_user,
):
    client_request.login(platform_admin_user)
    page = client_request.get(endpoint, service_id=SERVICE_ONE_ID, **extra_args)
    permission_checkboxes = page.select("input[type=checkbox]")

    for idx in range(len(permission_checkboxes)):
        assert permission_checkboxes[idx]["name"] == "permissions_field"
    assert permission_checkboxes[0]["value"] == ServicePermission.VIEW_ACTIVITY
    assert permission_checkboxes[1]["value"] == ServicePermission.SEND_MESSAGES
    assert permission_checkboxes[2]["value"] == ServicePermission.MANAGE_TEMPLATES
    assert permission_checkboxes[3]["value"] == ServicePermission.MANAGE_SERVICE


@pytest.mark.parametrize(
    ("service_has_email_auth", "displays_auth_type"), [(True, True), (False, False)]
)
def test_manage_users_page_shows_member_auth_type_if_service_has_email_auth_activated(
    client_request,
    service_has_email_auth,
    service_one,
    mock_get_users_by_service,
    mock_get_invites_for_service,
    mock_get_template_folders,
    displays_auth_type,
):
    if service_has_email_auth:
        service_one["permissions"].append(ServicePermission.EMAIL_AUTH)
    page = client_request.get("main.manage_users", service_id=service_one["id"])
    assert bool(page.select_one(".tick-cross-list-hint")) == displays_auth_type


@pytest.mark.parametrize(
    ("sms_option_disabled", "mobile_number", "expected_label"),
    [
        (
            True,
            None,
            """
            Text message code
            Not available because this team member has not added a
            phone number to their profile
        """,
        ),
        (
            False,
            "202-867-5303",
            """
            Text message code
        """,
        ),
    ],
)
def test_user_with_no_mobile_number_cant_be_set_to_sms_auth(
    client_request,
    mock_get_users_by_service,
    mock_get_template_folders,
    sms_option_disabled,
    mobile_number,
    expected_label,
    service_one,
    mocker,
    active_user_with_permissions,
):
    active_user_with_permissions["mobile_number"] = mobile_number

    service_one["permissions"].append(ServicePermission.EMAIL_AUTH)
    mocker.patch(
        "app.user_api_client.get_user", return_value=active_user_with_permissions
    )

    page = client_request.get(
        "main.edit_user_permissions",
        service_id=service_one["id"],
        user_id=sample_uuid(),
    )

    sms_auth_radio_button = page.select_one('input[value="sms_auth"]')
    assert sms_auth_radio_button.has_attr("disabled") == sms_option_disabled
    assert normalize_spaces(
        page.select_one("label[for=login_authentication-0]").text
    ) == normalize_spaces(expected_label)


@pytest.mark.parametrize(
    ("endpoint", "extra_args", "expected_checkboxes"),
    [
        (
            "main.edit_user_permissions",
            {"user_id": sample_uuid()},
            [
                (ServicePermission.VIEW_ACTIVITY, True),
                (ServicePermission.SEND_MESSAGES, True),
                (ServicePermission.MANAGE_TEMPLATES, True),
                (ServicePermission.MANAGE_SERVICE, True),
            ],
        ),
        (
            "main.invite_user",
            {},
            [
                (ServicePermission.VIEW_ACTIVITY, False),
                (ServicePermission.SEND_MESSAGES, False),
                (ServicePermission.MANAGE_TEMPLATES, False),
                (ServicePermission.MANAGE_SERVICE, False),
            ],
        ),
    ],
)
def test_should_show_page_for_one_user(
    client_request,
    mock_get_users_by_service,
    mock_get_template_folders,
    endpoint,
    extra_args,
    expected_checkboxes,
    platform_admin_user,
):
    client_request.login(platform_admin_user)
    page = client_request.get(endpoint, service_id=SERVICE_ONE_ID, **extra_args)
    checkboxes = page.select("input[type=checkbox]")

    assert len(checkboxes) == 4

    for index, expected in enumerate(expected_checkboxes):
        expected_input_value, expected_checked = expected
        assert checkboxes[index]["name"] == "permissions_field"
        assert checkboxes[index]["value"] == expected_input_value
        assert checkboxes[index].has_attr("checked") == expected_checked


def test_invite_user_allows_to_choose_auth(
    client_request,
    mock_get_users_by_service,
    mock_get_template_folders,
    service_one,
    platform_admin_user,
):
    service_one["permissions"].append(ServicePermission.EMAIL_AUTH)
    client_request.login(platform_admin_user)
    page = client_request.get("main.invite_user", service_id=SERVICE_ONE_ID)

    radio_buttons = page.select("input[name=login_authentication]")
    values = {button["value"] for button in radio_buttons}

    assert values == {"sms_auth", "email_auth"}
    assert not any(button.has_attr("disabled") for button in radio_buttons)


def test_invite_user_has_correct_email_field(
    client_request,
    mock_get_users_by_service,
    mock_get_template_folders,
    platform_admin_user,
    service_one,
    mocker,
):
    mocker.patch("app.models.user.InvitedUsers.client_method", return_value=[])
    mocker.patch(
        "app.models.user.Users.client_method", return_value=[platform_admin_user]
    )
    client_request.login(platform_admin_user)
    email_field = client_request.get(
        "main.invite_user", service_id=SERVICE_ONE_ID
    ).select_one("#email_address")
    assert email_field["spellcheck"] == "false"
    assert "autocomplete" not in email_field


def test_should_not_show_page_for_non_team_member(
    client_request,
    mock_get_users_by_service,
):
    client_request.get(
        "main.edit_user_permissions",
        service_id=SERVICE_ONE_ID,
        user_id=USER_ONE_ID,
        _expected_status=404,
    )


@pytest.mark.parametrize(
    ("submitted_permissions", "permissions_sent_to_api"),
    [
        (
            {
                "permissions_field": [
                    ServicePermission.VIEW_ACTIVITY,
                    ServicePermission.SEND_MESSAGES,
                    ServicePermission.MANAGE_TEMPLATES,
                    ServicePermission.MANAGE_SERVICE,
                ]
            },
            {
                ServicePermission.VIEW_ACTIVITY,
                ServicePermission.SEND_MESSAGES,
                ServicePermission.MANAGE_SERVICE,
                ServicePermission.MANAGE_TEMPLATES,
            },
        ),
        (
            {
                "permissions_field": [
                    ServicePermission.VIEW_ACTIVITY,
                    ServicePermission.SEND_MESSAGES,
                    ServicePermission.MANAGE_TEMPLATES,
                ]
            },
            {
                ServicePermission.VIEW_ACTIVITY,
                ServicePermission.SEND_MESSAGES,
                ServicePermission.MANAGE_TEMPLATES,
            },
        ),
        (
            {},
            set(),
        ),
    ],
)
def test_edit_user_permissions(
    client_request,
    mocker,
    mock_get_users_by_service,
    mock_get_invites_for_service,
    mock_set_user_permissions,
    mock_get_template_folders,
    fake_uuid,
    submitted_permissions,
    permissions_sent_to_api,
):
    client_request.post(
        "main.edit_user_permissions",
        service_id=SERVICE_ONE_ID,
        user_id=fake_uuid,
        _data=dict(email_address="test@example.com", **submitted_permissions),
        _expected_status=302,
        _expected_redirect=url_for(
            "main.manage_users",
            service_id=SERVICE_ONE_ID,
        ),
    )
    mock_set_user_permissions.assert_called_with(
        fake_uuid,
        SERVICE_ONE_ID,
        permissions=permissions_sent_to_api,
        folder_permissions=[],
    )


def test_edit_user_folder_permissions(
    client_request,
    mocker,
    service_one,
    mock_get_users_by_service,
    mock_get_invites_for_service,
    mock_set_user_permissions,
    mock_get_template_folders,
    fake_uuid,
):
    mock_get_template_folders.return_value = [
        {
            "id": "folder-id-1",
            "name": "folder_one",
            "parent_id": None,
            "users_with_permission": [],
        },
        {
            "id": "folder-id-2",
            "name": "folder_one",
            "parent_id": None,
            "users_with_permission": [],
        },
        {
            "id": "folder-id-3",
            "name": "folder_one",
            "parent_id": "folder-id-1",
            "users_with_permission": [],
        },
    ]

    page = client_request.get(
        "main.edit_user_permissions",
        service_id=SERVICE_ONE_ID,
        user_id=fake_uuid,
    )
    assert [
        item["value"] for item in page.select("input[name=folder_permissions]")
    ] == ["folder-id-1", "folder-id-3", "folder-id-2"]

    client_request.post(
        "main.edit_user_permissions",
        service_id=SERVICE_ONE_ID,
        user_id=fake_uuid,
        _data=dict(folder_permissions=["folder-id-1", "folder-id-3"]),
        _expected_status=302,
        _expected_redirect=url_for(
            "main.manage_users",
            service_id=SERVICE_ONE_ID,
        ),
    )
    mock_set_user_permissions.assert_called_with(
        fake_uuid,
        SERVICE_ONE_ID,
        permissions=set(),
        folder_permissions=["folder-id-1", "folder-id-3"],
    )


def test_cant_edit_user_folder_permissions_for_platform_admin_users(
    client_request,
    mocker,
    service_one,
    mock_get_users_by_service,
    mock_get_invites_for_service,
    mock_set_user_permissions,
    mock_get_template_folders,
    platform_admin_user,
):
    service_one["permissions"] = [ServicePermission.EDIT_FOLDER_PERMISSIONS]
    mocker.patch("app.user_api_client.get_user", return_value=platform_admin_user)
    mock_get_template_folders.return_value = [
        {
            "id": "folder-id-1",
            "name": "folder_one",
            "parent_id": None,
            "users_with_permission": [],
        },
        {
            "id": "folder-id-2",
            "name": "folder_one",
            "parent_id": None,
            "users_with_permission": [],
        },
        {
            "id": "folder-id-3",
            "name": "folder_one",
            "parent_id": "folder-id-1",
            "users_with_permission": [],
        },
    ]
    page = client_request.get(
        "main.edit_user_permissions",
        service_id=SERVICE_ONE_ID,
        user_id=platform_admin_user["id"],
    )
    assert (
        normalize_spaces(page.select("main .usa-body")[0].text)
        == "platform@admin.gsa.gov Change email address"
    )
    assert normalize_spaces(page.select("main .usa-body")[1].text) == (
        "Platform admin users can access all template folders."
    )
    assert page.select("input[name=folder_permissions]") == []
    client_request.post(
        "main.edit_user_permissions",
        service_id=SERVICE_ONE_ID,
        user_id=platform_admin_user["id"],
        _data={},
        _expected_status=302,
        _expected_redirect=url_for(
            "main.manage_users",
            service_id=SERVICE_ONE_ID,
        ),
    )
    mock_set_user_permissions.assert_called_with(
        platform_admin_user["id"],
        SERVICE_ONE_ID,
        permissions={
            ServicePermission.MANAGE_SERVICE,
            ServicePermission.MANAGE_TEMPLATES,
            ServicePermission.SEND_MESSAGES,
            ServicePermission.VIEW_ACTIVITY,
        },
        folder_permissions=None,
    )


def test_cant_edit_non_member_user_permissions(
    client_request,
    mocker,
    mock_get_users_by_service,
    mock_set_user_permissions,
):
    client_request.post(
        "main.edit_user_permissions",
        service_id=SERVICE_ONE_ID,
        user_id=USER_ONE_ID,
        _data={
            "email_address": "test@example.com",
            ServicePermission.MANAGE_SERVICE: "y",
        },
        _expected_status=404,
    )
    assert mock_set_user_permissions.called is False


def test_edit_user_permissions_including_authentication_with_email_auth_service(
    client_request,
    service_one,
    active_user_with_permissions,
    mock_get_users_by_service,
    mock_get_invites_for_service,
    mock_set_user_permissions,
    mock_update_user_attribute,
    mock_get_template_folders,
):
    active_user_with_permissions["auth_type"] = "email_auth"
    service_one["permissions"].append(ServicePermission.EMAIL_AUTH)

    client_request.post(
        "main.edit_user_permissions",
        service_id=SERVICE_ONE_ID,
        user_id=active_user_with_permissions["id"],
        _data={
            "email_address": active_user_with_permissions["email_address"],
            "permissions_field": [
                ServicePermission.SEND_MESSAGES,
                ServicePermission.MANAGE_TEMPLATES,
                ServicePermission.MANAGE_SERVICE,
            ],
            "login_authentication": "sms_auth",
        },
        _expected_status=302,
        _expected_redirect=url_for(
            "main.manage_users",
            service_id=SERVICE_ONE_ID,
        ),
    )

    mock_set_user_permissions.assert_called_with(
        str(active_user_with_permissions["id"]),
        SERVICE_ONE_ID,
        permissions={
            ServicePermission.SEND_MESSAGES,
            ServicePermission.MANAGE_TEMPLATES,
            ServicePermission.MANAGE_SERVICE,
        },
        folder_permissions=[],
    )
    mock_update_user_attribute.assert_called_with(
        str(active_user_with_permissions["id"]), auth_type="sms_auth"
    )


def test_edit_user_permissions_shows_authentication_for_email_auth_service(
    client_request,
    service_one,
    mock_get_users_by_service,
    mock_get_template_folders,
    active_user_with_permissions,
):
    service_one["permissions"].append(ServicePermission.EMAIL_AUTH)

    page = client_request.get(
        "main.edit_user_permissions",
        service_id=SERVICE_ONE_ID,
        user_id=active_user_with_permissions["id"],
    )

    radio_buttons = page.select("input[name=login_authentication]")
    values = {button["value"] for button in radio_buttons}

    assert values == {"sms_auth", "email_auth"}
    assert not any(button.has_attr("disabled") for button in radio_buttons)


def test_should_show_page_for_inviting_user(
    client_request,
    mock_get_template_folders,
    active_user_with_permissions,
):
    client_request.login(active_user_with_permissions)
    page = client_request.get(
        "main.invite_user",
        service_id=SERVICE_ONE_ID,
    )

    assert "Invite a team member" in page.find("h1").text.strip()
    assert not page.find("div", class_="checkboxes-nested")


def test_should_not_show_page_for_inviting_user_without_permissions(
    client_request, mock_get_template_folders, active_user_empty_permissions
):
    client_request.login(active_user_empty_permissions)
    page = client_request.get(
        "main.invite_user", service_id=SERVICE_ONE_ID, _expected_status=403
    )

    assert "not allowed to see this page" in page.h1.string.strip()


def test_should_show_page_for_inviting_user_with_email_prefilled(
    client_request,
    mocker,
    service_one,
    mock_get_template_folders,
    fake_uuid,
    active_user_with_permissions,
    active_user_with_permission_to_other_service,
    mock_get_organization_by_domain,
    mock_get_invites_for_service,
):
    client_request.login(active_user_with_permissions)
    service_one["organization"] = ORGANISATION_ID
    mocker.patch(
        "app.models.user.user_api_client.get_user",
        side_effect=[
            active_user_with_permission_to_other_service,
        ],
    )

    page = client_request.get(
        "main.invite_user",
        service_id=SERVICE_ONE_ID,
        user_id=fake_uuid,
        # We have the user’s name in the H1 but don’t want it duplicated
        # in the page title
        _test_page_title=False,
    )
    assert normalize_spaces(page.select_one("title").text).startswith(
        "Invite a team member"
    )
    assert normalize_spaces(page.select_one("h1").text) == ("Invite Service Two User")
    assert not page.select("input#email_address") or page.select("input[type=email]")


def test_should_show_page_if_prefilled_user_is_already_a_team_member(
    mocker,
    client_request,
    mock_get_template_folders,
    fake_uuid,
    active_user_with_permissions,
    active_caseworking_user,
):
    client_request.login(active_user_with_permissions)
    mocker.patch(
        "app.models.user.user_api_client.get_user",
        side_effect=[
            active_caseworking_user,
        ],
    )
    page = client_request.get(
        "main.invite_user",
        service_id=SERVICE_ONE_ID,
        user_id=fake_uuid,
    )

    assert normalize_spaces(page.select_one("title").text).startswith(
        "This person is already a team member"
    )
    assert normalize_spaces(page.select_one("h1").text) == (
        "This person is already a team member"
    )
    assert normalize_spaces(page.select_one("main p").text) == (
        "Test User is already member of ‘service one’."
    )
    assert not page.select("form")


def test_should_show_page_if_prefilled_user_is_already_invited(
    mocker,
    client_request,
    mock_get_template_folders,
    fake_uuid,
    active_user_with_permission_to_other_service,
    mock_get_invites_for_service,
    platform_admin_user,
):
    active_user_with_permission_to_other_service["email_address"] = (
        "user_1@testnotify.gsa.gov"
    )
    client_request.login(platform_admin_user)
    mocker.patch(
        "app.models.user.user_api_client.get_user",
        side_effect=[
            active_user_with_permission_to_other_service,
        ],
    )
    page = client_request.get(
        "main.invite_user",
        service_id=SERVICE_ONE_ID,
        user_id=fake_uuid,
    )

    assert normalize_spaces(page.select_one("title").text).startswith(
        "This person has already received an invite"
    )
    assert normalize_spaces(page.select_one("h1").text) == (
        "This person has already received an invite"
    )
    assert normalize_spaces(page.select_one("main .usa-body").text) == (
        "Service Two User has not accepted their invitation to "
        "‘service one’ yet. You do not need to do anything."
    )
    assert not page.select("form")


def test_should_403_if_trying_to_prefill_email_address_for_user_with_no_organization(
    mocker,
    client_request,
    service_one,
    mock_get_template_folders,
    fake_uuid,
    active_user_with_permissions,
    active_user_with_permission_to_other_service,
    mock_get_invites_for_service,
    mock_get_no_organization_by_domain,
):
    service_one["organization"] = ORGANISATION_ID
    client_request.login(active_user_with_permissions)
    mocker.patch(
        "app.models.user.user_api_client.get_user",
        side_effect=[
            active_user_with_permission_to_other_service,
        ],
    )
    client_request.get(
        "main.invite_user",
        service_id=SERVICE_ONE_ID,
        user_id=fake_uuid,
        _expected_status=403,
    )


def test_should_403_if_trying_to_prefill_email_address_for_user_from_other_organization(
    mocker,
    client_request,
    service_one,
    mock_get_template_folders,
    fake_uuid,
    active_user_with_permissions,
    active_user_with_permission_to_other_service,
    mock_get_invites_for_service,
    mock_get_organization_by_domain,
):
    service_one["organization"] = ORGANISATION_TWO_ID
    client_request.login(active_user_with_permissions)
    mocker.patch(
        "app.models.user.user_api_client.get_user",
        side_effect=[
            active_user_with_permission_to_other_service,
        ],
    )
    client_request.get(
        "main.invite_user",
        service_id=SERVICE_ONE_ID,
        user_id=fake_uuid,
        _expected_status=403,
    )


def test_should_show_folder_permission_form_if_service_has_folder_permissions_enabled(
    client_request, mocker, mock_get_template_folders, service_one, platform_admin_user
):
    client_request.login(platform_admin_user)
    mock_get_template_folders.return_value = [
        {
            "id": "folder-id-1",
            "name": "folder_one",
            "parent_id": None,
            "users_with_permission": [],
        },
        {
            "id": "folder-id-2",
            "name": "folder_two",
            "parent_id": None,
            "users_with_permission": [],
        },
        {
            "id": "folder-id-3",
            "name": "folder_three",
            "parent_id": "folder-id-1",
            "users_with_permission": [],
        },
    ]
    page = client_request.get(
        "main.invite_user",
        service_id=SERVICE_ONE_ID,
    )

    assert "Invite a team member" in page.find("h1").text.strip()

    folder_checkboxes = page.find("div", class_="selection-wrapper").find_all("li")
    assert len(folder_checkboxes) == 3


@pytest.mark.parametrize(
    ("email_address", "gov_user"),
    [("test@example.gsa.gov", True), ("test@example.com", False)],
)
def test_invite_user(
    client_request,
    platform_admin_user,
    mocker,
    sample_invite,
    email_address,
    gov_user,
    mock_get_template_folders,
    mock_get_organizations,
):
    sample_invite["email_address"] = email_address

    assert is_gov_user(email_address) == gov_user
    mocker.patch(
        "app.models.user.InvitedUsers.client_method", return_value=[sample_invite]
    )
    mocker.patch(
        "app.models.user.Users.client_method",
        return_value=[platform_admin_user],
    )
    mocker.patch("app.invite_api_client.create_invite", return_value=sample_invite)
    client_request.login(platform_admin_user)
    page = client_request.post(
        "main.invite_user",
        service_id=SERVICE_ONE_ID,
        _data={
            "email_address": email_address,
            "permissions_field": [
                ServicePermission.VIEW_ACTIVITY,
                ServicePermission.SEND_MESSAGES,
                ServicePermission.MANAGE_TEMPLATES,
                ServicePermission.MANAGE_SERVICE,
            ],
        },
        _follow_redirects=True,
    )
    assert page.h1.string.strip() == "Team members"
    flash_banner = page.find("div", class_="banner-default-with-tick").string.strip()
    assert flash_banner == f"Invite sent to {email_address}"

    expected_permissions = {
        ServicePermission.MANAGE_SERVICE,
        ServicePermission.MANAGE_TEMPLATES,
        ServicePermission.SEND_MESSAGES,
        ServicePermission.VIEW_ACTIVITY,
    }

    app.invite_api_client.create_invite.assert_called_once_with(
        sample_invite["from_user"],
        sample_invite["service"],
        email_address,
        expected_permissions,
        "sms_auth",
        [],
    )


def test_invite_user_when_email_address_is_prefilled(
    client_request,
    service_one,
    platform_admin_user,
    active_user_with_permission_to_other_service,
    fake_uuid,
    mocker,
    sample_invite,
    mock_get_template_folders,
    mock_get_invites_for_service,
    mock_get_organization_by_domain,
):
    service_one["organization"] = ORGANISATION_ID
    client_request.login(platform_admin_user)
    mocker.patch(
        "app.models.user.user_api_client.get_user",
        side_effect=[
            active_user_with_permission_to_other_service,
        ],
    )
    mocker.patch("app.invite_api_client.create_invite", return_value=sample_invite)
    client_request.post(
        "main.invite_user",
        service_id=SERVICE_ONE_ID,
        user_id=fake_uuid,
        _data={
            # No posted email address
            "permissions_field": [
                ServicePermission.SEND_MESSAGES,
            ],
        },
    )

    app.invite_api_client.create_invite.assert_called_once_with(
        platform_admin_user["id"],
        SERVICE_ONE_ID,
        active_user_with_permission_to_other_service["email_address"],
        {"send_messages"},
        "sms_auth",
        [],
    )


@pytest.mark.parametrize("auth_type", [("sms_auth"), ("email_auth")])
@pytest.mark.parametrize(
    ("email_address", "gov_user"),
    [("test@example.gsa.gov", True), ("test@example.com", False)],
)
def test_invite_user_with_email_auth_service(
    client_request,
    service_one,
    platform_admin_user,
    sample_invite,
    email_address,
    gov_user,
    mocker,
    auth_type,
    mock_get_organizations,
    mock_get_template_folders,
):
    service_one["permissions"].append(ServicePermission.EMAIL_AUTH)
    sample_invite["email_address"] = "test@example.gsa.gov"

    assert is_gov_user(email_address) is gov_user
    mocker.patch(
        "app.models.user.InvitedUsers.client_method", return_value=[sample_invite]
    )
    mocker.patch(
        "app.models.user.Users.client_method",
        return_value=[platform_admin_user],
    )
    mocker.patch("app.invite_api_client.create_invite", return_value=sample_invite)

    client_request.login(platform_admin_user)
    page = client_request.post(
        "main.invite_user",
        service_id=SERVICE_ONE_ID,
        _data={
            "email_address": email_address,
            "permissions_field": [
                ServicePermission.VIEW_ACTIVITY,
                ServicePermission.SEND_MESSAGES,
                ServicePermission.MANAGE_TEMPLATES,
                ServicePermission.MANAGE_SERVICE,
            ],
            "login_authentication": auth_type,
        },
        _follow_redirects=True,
        _expected_status=200,
    )

    assert page.h1.string.strip() == "Team members"
    flash_banner = page.find("div", class_="banner-default-with-tick").string.strip()
    assert flash_banner == "Invite sent to test@example.gsa.gov"

    expected_permissions = {
        ServicePermission.MANAGE_SERVICE,
        ServicePermission.MANAGE_TEMPLATES,
        ServicePermission.SEND_MESSAGES,
        ServicePermission.VIEW_ACTIVITY,
    }

    app.invite_api_client.create_invite.assert_called_once_with(
        sample_invite["from_user"],
        sample_invite["service"],
        email_address,
        expected_permissions,
        auth_type,
        [],
    )


def test_resend_expired_invitation(
    client_request,
    mock_get_invites_for_service,
    expired_invite,
    active_user_with_permissions,
    mock_get_users_by_service,
    mock_get_template_folders,
    mocker,
):
    mock_resend = mocker.patch("app.invite_api_client.resend_invite")
    mocker.patch(
        "app.invite_api_client.get_invited_user_for_service",
        return_value=expired_invite,
    )
    page = client_request.get(
        "main.resend_invite",
        service_id=SERVICE_ONE_ID,
        invited_user_id=expired_invite["id"],
        _follow_redirects=True,
    )
    assert normalize_spaces(page.h1.text) == "Team members"
    assert mock_resend.called
    called_args = set(mock_resend.call_args.args) | set(
        mock_resend.call_args.kwargs.values()
    )
    assert SERVICE_ONE_ID in called_args
    assert expired_invite["id"] in called_args


def test_cancel_invited_user_cancels_user_invitations(
    client_request,
    mock_get_invites_for_service,
    sample_invite,
    active_user_with_permissions,
    mock_get_users_by_service,
    mock_get_template_folders,
    mocker,
):
    mock_cancel = mocker.patch("app.invite_api_client.cancel_invited_user")
    mocker.patch(
        "app.invite_api_client.get_invited_user_for_service",
        return_value=sample_invite,
    )

    page = client_request.get(
        "main.cancel_invited_user",
        service_id=SERVICE_ONE_ID,
        invited_user_id=sample_invite["id"],
        _follow_redirects=True,
    )

    assert normalize_spaces(page.h1.text) == "Team members"
    flash_banner = normalize_spaces(
        page.find("div", class_="banner-default-with-tick").text
    )
    assert flash_banner == f"Invitation cancelled for {sample_invite['email_address']}"
    mock_cancel.assert_called_once_with(
        service_id=SERVICE_ONE_ID,
        invited_user_id=sample_invite["id"],
    )


def test_cancel_invited_user_doesnt_work_if_user_not_invited_to_this_service(
    client_request,
    mock_get_invites_for_service,
    mocker,
):
    mock_cancel = mocker.patch("app.invite_api_client.cancel_invited_user")
    client_request.get(
        "main.cancel_invited_user",
        service_id=SERVICE_ONE_ID,
        invited_user_id=sample_uuid(),
        _expected_status=404,
    )
    assert mock_cancel.called is False


@pytest.mark.parametrize(
    ("invite_status", "expected_text"),
    [
        (
            "pending",
            (
                "invited_user@test.gsa.gov "
                "invited_user@test.gsa.gov (invited) "
                "Permissions "
                "Can See dashboard "
                "Can Send messages "
                "Can Manage settings, team and usage "
                "Cancel invitation for invited_user@test.gsa.gov"
            ),
        ),
        # Test case removed due to the removal of canceled users from the dashboard
        # (
        #     "cancelled",
        #     (
        #         "invited_user@test.gsa.gov(cancelled invite) "
        #         "Permissions"
        #         # all permissions are greyed out
        #     ),
        # ),
    ],
)
def test_manage_users_shows_invited_user(
    client_request,
    mocker,
    active_user_with_permissions,
    mock_get_template_folders,
    sample_invite,
    invite_status,
    expected_text,
):
    sample_invite["status"] = invite_status
    mocker.patch(
        "app.models.user.InvitedUsers.client_method", return_value=[sample_invite]
    )
    mocker.patch(
        "app.models.user.Users.client_method",
        return_value=[active_user_with_permissions],
    )

    page = client_request.get("main.manage_users", service_id=SERVICE_ONE_ID)
    assert page.h1.string.strip() == "Team members"
    assert normalize_spaces(page.select(".user-list-item")[0].text) == expected_text


def test_manage_users_does_not_show_accepted_invite(
    client_request,
    mocker,
    active_user_with_permissions,
    sample_invite,
    mock_get_template_folders,
):
    invited_user_id = uuid.uuid4()
    sample_invite["id"] = invited_user_id
    sample_invite["status"] = "accepted"
    mocker.patch(
        "app.models.user.InvitedUsers.client_method", return_value=[sample_invite]
    )
    mocker.patch(
        "app.models.user.Users.client_method",
        return_value=[active_user_with_permissions],
    )

    page = client_request.get("main.manage_users", service_id=SERVICE_ONE_ID)

    assert page.h1.string.strip() == "Team members"
    user_lists = page.find_all("div", {"class": "user-list"})
    assert len(user_lists) == 1
    assert not page.find(text="invited_user@test.gsa.gov")


def test_user_cant_invite_themselves(
    client_request,
    mocker,
    active_user_with_permissions,
    mock_create_invite,
    mock_get_template_folders,
):
    page = client_request.post(
        "main.invite_user",
        service_id=SERVICE_ONE_ID,
        _data={
            "email_address": active_user_with_permissions["email_address"],
            "permissions_field": [
                ServicePermission.SEND_MESSAGES,
                ServicePermission.MANAGE_SERVICE,
            ],
        },
        _follow_redirects=True,
        _expected_status=200,
    )
    assert page.h1.string.strip() == "Invite a team member"
    form_error = page.find("span", class_="usa-error-message").text.strip()
    assert form_error == "Error: You cannot send an invitation to yourself"
    assert not mock_create_invite.called


def test_user_cant_invite_themselves_platform_admin(
    client_request,
    mocker,
    mock_create_invite,
    mock_get_template_folders,
):
    platform_admin = create_platform_admin_user()
    client_request.login(platform_admin)
    page = client_request.post(
        "main.invite_user",
        service_id=SERVICE_ONE_ID,
        _follow_redirects=True,
        _expected_status=200,
    )
    assert "Invite a team member" in page.h1.string.strip()


def test_no_permission_manage_users_page(
    client_request,
    service_one,
    mock_get_users_by_service,
    mock_get_invites_for_service,
    mock_get_template_folders,
    api_user_active,
    mocker,
):
    resp_text = client_request.get("main.manage_users", service_id=service_one["id"])
    assert url_for(".invite_user", service_id=service_one["id"]) not in resp_text
    assert "Edit permission" not in resp_text
    assert "Team members" not in resp_text


@pytest.mark.parametrize(
    ("folders_user_can_see", "expected_message"),
    [
        (3, "Can see all folders"),
        (2, "Can see 2 folders"),
        (1, "Can see 1 folder"),
        (0, "Cannot see any folders"),
    ],
)
def test_manage_user_page_shows_how_many_folders_user_can_view(
    client_request,
    service_one,
    mock_get_template_folders,
    mock_get_users_by_service,
    mock_get_invites_for_service,
    api_user_active,
    folders_user_can_see,
    expected_message,
):
    service_one["permissions"] = [ServicePermission.EDIT_FOLDER_PERMISSIONS]
    mock_get_template_folders.return_value = [
        {
            "id": "folder-id-1",
            "name": "f1",
            "parent_id": None,
            "users_with_permission": [],
        },
        {
            "id": "folder-id-2",
            "name": "f2",
            "parent_id": None,
            "users_with_permission": [],
        },
        {
            "id": "folder-id-3",
            "name": "f3",
            "parent_id": None,
            "users_with_permission": [],
        },
    ]
    for i in range(folders_user_can_see):
        mock_get_template_folders.return_value[i]["users_with_permission"].append(
            api_user_active["id"]
        )

    page = client_request.get("main.manage_users", service_id=service_one["id"])

    user_div = page.select_one(
        "h2[title='notify@digital.cabinet-office.gov.uk']"
    ).parent
    assert user_div.select_one(".tick-cross-list-hint").text.strip() == expected_message


def test_manage_user_page_doesnt_show_folder_hint_if_service_has_no_folders(
    client_request,
    service_one,
    mock_get_template_folders,
    mock_get_users_by_service,
    mock_get_invites_for_service,
    api_user_active,
):
    service_one["permissions"] = [ServicePermission.EDIT_FOLDER_PERMISSIONS]
    mock_get_template_folders.return_value = []

    page = client_request.get("main.manage_users", service_id=service_one["id"])

    user_div = page.select_one(
        "h2[title='notify@digital.cabinet-office.gov.uk']"
    ).parent
    assert user_div.find(".tick-cross-list-hint:last-child") is None


def test_manage_user_page_doesnt_show_folder_hint_if_service_cant_edit_folder_permissions(
    client_request,
    service_one,
    mock_get_template_folders,
    mock_get_users_by_service,
    mock_get_invites_for_service,
    api_user_active,
):
    service_one["permissions"] = []
    mock_get_template_folders.return_value = [
        {
            "id": "folder-id-1",
            "name": "f1",
            "parent_id": None,
            "users_with_permission": [api_user_active["id"]],
        },
    ]

    page = client_request.get("main.manage_users", service_id=service_one["id"])

    user_div = page.select_one(
        "h2[title='notify@digital.cabinet-office.gov.uk']"
    ).parent
    assert user_div.find(".tick-cross-list-hint:last-child") is None


def test_remove_user_from_service(
    client_request,
    active_user_with_permissions,
    api_user_active,
    service_one,
    mock_remove_user_from_service,
    mocker,
):
    mock_event_handler = mocker.patch(
        "app.main.views.manage_users.create_remove_user_from_service_event"
    )

    client_request.post(
        "main.remove_user_from_service",
        service_id=service_one["id"],
        user_id=active_user_with_permissions["id"],
        _expected_redirect=url_for("main.manage_users", service_id=service_one["id"]),
    )
    mock_remove_user_from_service.assert_called_once_with(
        service_one["id"], str(active_user_with_permissions["id"])
    )

    mock_event_handler.assert_called_once_with(
        user_id=active_user_with_permissions["id"],
        removed_by_id=api_user_active["id"],
        service_id=service_one["id"],
    )


def test_can_invite_user_as_platform_admin(
    client_request,
    service_one,
    platform_admin_user,
    active_user_with_permissions,
    mock_get_invites_for_service,
    mock_get_template_folders,
    mocker,
):
    mocker.patch(
        "app.models.user.Users.client_method",
        return_value=[active_user_with_permissions],
    )

    page = client_request.get(
        "main.manage_users",
        service_id=SERVICE_ONE_ID,
    )
    assert url_for(".invite_user", service_id=service_one["id"]) in str(page)


def test_edit_user_email_page(
    client_request,
    active_user_with_permissions,
    service_one,
    mock_get_users_by_service,
    mocker,
):
    user = active_user_with_permissions
    mocker.patch("app.user_api_client.get_user", return_value=user)

    page = client_request.get(
        "main.edit_user_email", service_id=service_one["id"], user_id=sample_uuid()
    )

    assert page.find("h1").text == "Change team member’s email address"
    assert page.select("p[id=user_name]")[
        0
    ].text == "This will change the email address for {}.".format(user["name"])
    assert page.select("input[type=email]")[0].attrs["value"] == user["email_address"]
    assert normalize_spaces(page.select("main button[type=submit]")[0].text) == "Save"


def test_edit_user_email_page_404_for_non_team_member(
    client_request,
    mock_get_users_by_service,
):
    client_request.get(
        "main.edit_user_email",
        service_id=SERVICE_ONE_ID,
        user_id=USER_ONE_ID,
        _expected_status=404,
    )


def test_edit_user_email_redirects_to_confirmation(
    client_request,
    active_user_with_permissions,
    mock_get_users_by_service,
    mock_get_user_by_email_not_found,
):
    client_request.post(
        "main.edit_user_email",
        service_id=SERVICE_ONE_ID,
        user_id=active_user_with_permissions["id"],
        _expected_status=302,
        _expected_redirect=url_for(
            "main.confirm_edit_user_email",
            service_id=SERVICE_ONE_ID,
            user_id=active_user_with_permissions["id"],
        ),
    )
    with client_request.session_transaction() as session:
        assert (
            session[
                "team_member_email_change-{}".format(active_user_with_permissions["id"])
            ]
            == "test@user.gsa.gov"
        )


def test_edit_user_email_without_changing_goes_back_to_team_members(
    client_request,
    active_user_with_permissions,
    mock_get_user_by_email,
    mock_get_users_by_service,
    mock_update_user_attribute,
):
    client_request.post(
        "main.edit_user_email",
        service_id=SERVICE_ONE_ID,
        user_id=active_user_with_permissions["id"],
        _data={"email_address": active_user_with_permissions["email_address"]},
        _expected_status=302,
        _expected_redirect=url_for(
            "main.manage_users",
            service_id=SERVICE_ONE_ID,
        ),
    )
    assert mock_update_user_attribute.called is False


@pytest.mark.parametrize("original_email_address", ["test@gsa.gov", "test@example.com"])
def test_edit_user_email_can_change_any_email_address_to_a_gov_email_address(
    client_request,
    active_user_with_permissions,
    mock_get_user_by_email_not_found,
    mock_get_users_by_service,
    mock_update_user_attribute,
    mock_get_organizations,
    original_email_address,
):
    active_user_with_permissions["email_address"] = original_email_address

    client_request.post(
        "main.edit_user_email",
        service_id=SERVICE_ONE_ID,
        user_id=active_user_with_permissions["id"],
        _data={"email_address": "new-email-address@gsa.gov"},
        _expected_status=302,
        _expected_redirect=url_for(
            "main.confirm_edit_user_email",
            service_id=SERVICE_ONE_ID,
            user_id=active_user_with_permissions["id"],
        ),
    )


def test_edit_user_email_can_change_a_non_gov_email_address_to_another_non_gov_email_address(
    client_request,
    active_user_with_permissions,
    mock_get_user_by_email_not_found,
    mock_get_users_by_service,
    mock_update_user_attribute,
    mock_get_organizations,
):
    active_user_with_permissions["email_address"] = "old@example.com"

    client_request.post(
        "main.edit_user_email",
        service_id=SERVICE_ONE_ID,
        user_id=active_user_with_permissions["id"],
        _data={"email_address": "new@example.com"},
        _expected_status=302,
        _expected_redirect=url_for(
            "main.confirm_edit_user_email",
            service_id=SERVICE_ONE_ID,
            user_id=active_user_with_permissions["id"],
        ),
    )


def test_edit_user_email_cannot_change_a_gov_email_address_to_a_non_gov_email_address(
    client_request,
    active_user_with_permissions,
    mock_get_user_by_email_not_found,
    mock_get_users_by_service,
    mock_update_user_attribute,
    mock_get_organizations,
):
    page = client_request.post(
        "main.edit_user_email",
        service_id=SERVICE_ONE_ID,
        user_id=active_user_with_permissions["id"],
        _data={"email_address": "new_email@example.com"},
        _expected_status=200,
    )
    assert (
        "Enter a public sector email address"
        in page.select_one(".usa-error-message").text
    )
    with client_request.session_transaction() as session:
        assert (
            "team_member_email_change-{}".format(active_user_with_permissions["id"])
            not in session
        )


def test_confirm_edit_user_email_page(
    client_request,
    active_user_with_permissions,
    mock_get_users_by_service,
    mock_get_user,
):
    new_email = "new_email@gsa.gov"
    with client_request.session_transaction() as session:
        session[
            "team_member_email_change-{}".format(active_user_with_permissions["id"])
        ] = new_email

    page = client_request.get(
        "main.confirm_edit_user_email",
        service_id=SERVICE_ONE_ID,
        user_id=active_user_with_permissions["id"],
    )

    assert "Confirm change of email address" in page.text
    for text in [
        "New email address:",
        new_email,
        "We will send {} an email to tell them about the change.".format(
            active_user_with_permissions["name"]
        ),
    ]:
        assert text in page.text
    assert "Confirm" in page.text


def test_confirm_edit_user_email_page_redirects_if_session_empty(
    client_request,
    mock_get_users_by_service,
    active_user_with_permissions,
):
    page = client_request.get(
        "main.confirm_edit_user_email",
        service_id=SERVICE_ONE_ID,
        user_id=active_user_with_permissions["id"],
        _follow_redirects=True,
    )
    assert "Confirm change of email address" not in page.text


def test_confirm_edit_user_email_page_404s_for_non_team_member(
    client_request,
    mock_get_users_by_service,
):
    client_request.get(
        "main.confirm_edit_user_email",
        service_id=SERVICE_ONE_ID,
        user_id=USER_ONE_ID,
        _expected_status=404,
    )


def test_confirm_edit_user_email_changes_user_email(
    client_request,
    active_user_with_permissions,
    api_user_active,
    service_one,
    mocker,
    mock_update_user_attribute,
):
    # We want active_user_with_permissions (the current user) to update the email address for api_user_active
    # By default both users would have the same id, so we change the id of api_user_active
    api_user_active["id"] = str(uuid.uuid4())
    mocker.patch(
        "app.models.user.Users.client_method",
        return_value=[api_user_active, active_user_with_permissions],
    )
    # get_user gets called twice - first to check if current user can see the page, then to see if the team member
    # whose email address we're changing belongs to the service
    mocker.patch(
        "app.user_api_client.get_user",
        side_effect=[active_user_with_permissions, api_user_active],
    )
    mock_event_handler = mocker.patch(
        "app.main.views.manage_users.create_email_change_event"
    )

    new_email = "new_email@gsa.gov"
    with client_request.session_transaction() as session:
        session["team_member_email_change-{}".format(api_user_active["id"])] = new_email

    client_request.post(
        "main.confirm_edit_user_email",
        service_id=service_one["id"],
        user_id=api_user_active["id"],
        _expected_status=302,
        _expected_redirect=url_for(
            "main.manage_users",
            service_id=SERVICE_ONE_ID,
        ),
    )

    mock_update_user_attribute.assert_called_once_with(
        api_user_active["id"],
        email_address=new_email,
        updated_by=active_user_with_permissions["id"],
    )
    mock_event_handler.assert_called_once_with(
        user_id=api_user_active["id"],
        updated_by_id=active_user_with_permissions["id"],
        original_email_address=api_user_active["email_address"],
        new_email_address=new_email,
    )


def test_confirm_edit_user_email_doesnt_change_user_email_for_non_team_member(
    client_request,
    mock_get_users_by_service,
):
    with client_request.session_transaction() as session:
        session["team_member_email_change"] = "new_email@gsa.gov"
    client_request.post(
        "main.confirm_edit_user_email",
        service_id=SERVICE_ONE_ID,
        user_id=USER_ONE_ID,
        _expected_status=404,
    )


def test_edit_user_permissions_page_displays_redacted_mobile_number_and_change_link(
    client_request,
    active_user_with_permissions,
    mock_get_users_by_service,
    mock_get_template_folders,
    service_one,
    mocker,
):
    page = client_request.get(
        "main.edit_user_permissions",
        service_id=service_one["id"],
        user_id=active_user_with_permissions["id"],
    )

    assert active_user_with_permissions["name"] in page.find("h1").text
    mobile_number_paragraph = page.select("p[id=user_mobile_number]")[0]
    assert "202-8 •  •  •  • 303" in mobile_number_paragraph.text
    change_link = mobile_number_paragraph.findChild()
    assert change_link.attrs[
        "href"
    ] == "/services/{}/users/{}/edit-mobile-number".format(
        service_one["id"], active_user_with_permissions["id"]
    )


def test_edit_user_permissions_with_delete_query_shows_banner(
    client_request,
    active_user_with_permissions,
    mock_get_users_by_service,
    mock_get_template_folders,
    service_one,
):
    page = client_request.get(
        "main.edit_user_permissions",
        service_id=service_one["id"],
        user_id=active_user_with_permissions["id"],
        delete=1,
    )

    banner = page.find("div", class_="banner-dangerous")
    assert banner.contents[0].strip() == "Are you sure you want to remove Test User?"
    assert banner.form.attrs["action"] == url_for(
        "main.remove_user_from_service",
        service_id=service_one["id"],
        user_id=active_user_with_permissions["id"],
    )


def test_edit_user_mobile_number_page(
    client_request,
    active_user_with_permissions,
    mock_get_users_by_service,
    service_one,
    mocker,
):
    page = client_request.get(
        "main.edit_user_mobile_number",
        service_id=service_one["id"],
        user_id=active_user_with_permissions["id"],
    )

    assert page.find("h1").text == "Change team member’s mobile number"
    assert page.select("p[id=user_name]")[0].text == (
        "This will change the mobile number for {}."
    ).format(active_user_with_permissions["name"])
    assert page.select("input[name=mobile_number]")[0].attrs["value"] == "202-8••••303"
    assert normalize_spaces(page.select("main button[type=submit]")[0].text) == "Save"


def test_edit_user_mobile_number_redirects_to_confirmation(
    client_request,
    active_user_with_permissions,
    mock_get_users_by_service,
):
    client_request.post(
        "main.edit_user_mobile_number",
        service_id=SERVICE_ONE_ID,
        user_id=active_user_with_permissions["id"],
        _data={"mobile_number": "2028675309"},
        _expected_status=302,
        _expected_redirect=url_for(
            "main.confirm_edit_user_mobile_number",
            service_id=SERVICE_ONE_ID,
            user_id=active_user_with_permissions["id"],
        ),
    )


def test_edit_user_mobile_number_redirects_to_manage_users_if_number_not_changed(
    client_request,
    active_user_with_permissions,
    mock_get_users_by_service,
    service_one,
    mocker,
    mock_get_user,
):
    client_request.post(
        "main.edit_user_mobile_number",
        service_id=SERVICE_ONE_ID,
        user_id=active_user_with_permissions["id"],
        _data={"mobile_number": "202-8••••303"},
        _expected_status=302,
        _expected_redirect=url_for(
            "main.manage_users",
            service_id=SERVICE_ONE_ID,
        ),
    )


def test_confirm_edit_user_mobile_number_page(
    client_request,
    active_user_with_permissions,
    mock_get_users_by_service,
    service_one,
    mocker,
    mock_get_user,
):
    new_number = "2028675309"
    with client_request.session_transaction() as session:
        session["team_member_mobile_change"] = new_number
    page = client_request.get(
        "main.confirm_edit_user_mobile_number",
        service_id=SERVICE_ONE_ID,
        user_id=active_user_with_permissions["id"],
    )

    assert "Confirm change of mobile number" in page.text
    for text in [
        "New mobile number:",
        new_number,
        "We will send {} a text message to tell them about the change.".format(
            active_user_with_permissions["name"]
        ),
    ]:
        assert text in page.text
    assert "Confirm" in page.text


def test_confirm_edit_user_mobile_number_page_redirects_if_session_empty(
    client_request,
    active_user_with_permissions,
    mock_get_users_by_service,
    service_one,
    mocker,
    mock_get_user,
):
    page = client_request.get(
        "main.confirm_edit_user_mobile_number",
        service_id=SERVICE_ONE_ID,
        user_id=active_user_with_permissions["id"],
        _expected_status=302,
    )
    assert "Confirm change of mobile number" not in page.text


def test_confirm_edit_user_mobile_number_changes_user_mobile_number(
    client_request,
    active_user_with_permissions,
    api_user_active,
    service_one,
    mocker,
    mock_update_user_attribute,
):
    # We want active_user_with_permissions (the current user) to update the mobile number for api_user_active
    # By default both users would have the same id, so we change the id of api_user_active
    api_user_active["id"] = str(uuid.uuid4())

    mocker.patch(
        "app.models.user.Users.client_method",
        return_value=[api_user_active, active_user_with_permissions],
    )
    # get_user gets called twice - first to check if current user can see the page, then to see if the team member
    # whose mobile number we're changing belongs to the service
    mocker.patch(
        "app.user_api_client.get_user",
        side_effect=[active_user_with_permissions, api_user_active],
    )
    mock_event_handler = mocker.patch(
        "app.main.views.manage_users.create_mobile_number_change_event"
    )

    new_number = "2028675309"
    with client_request.session_transaction() as session:
        session["team_member_mobile_change"] = new_number

    client_request.post(
        "main.confirm_edit_user_mobile_number",
        service_id=SERVICE_ONE_ID,
        user_id=api_user_active["id"],
        _expected_status=302,
        _expected_redirect=url_for(
            "main.manage_users",
            service_id=SERVICE_ONE_ID,
        ),
    )
    mock_update_user_attribute.assert_called_once_with(
        api_user_active["id"],
        mobile_number=new_number,
        updated_by=active_user_with_permissions["id"],
    )
    mock_event_handler.assert_called_once_with(
        user_id=api_user_active["id"],
        updated_by_id=active_user_with_permissions["id"],
        original_mobile_number=api_user_active["mobile_number"],
        new_mobile_number=new_number,
    )


def test_confirm_edit_user_mobile_number_doesnt_change_user_mobile_for_non_team_member(
    client_request,
    mock_get_users_by_service,
):
    with client_request.session_transaction() as session:
        session["team_member_mobile_change"] = "2028675309"
    client_request.post(
        "main.confirm_edit_user_mobile_number",
        service_id=SERVICE_ONE_ID,
        user_id=USER_ONE_ID,
        _expected_status=404,
    )
