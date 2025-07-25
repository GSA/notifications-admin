from functools import partial
from unittest.mock import Mock, PropertyMock, call
from uuid import uuid4

import pytest
from flask import url_for
from freezegun import freeze_time

import app
from app.enums import ServicePermission
from notifications_python_client.errors import HTTPError
from tests import (
    find_element_by_tag_and_partial_text,
    organization_json,
    sample_uuid,
    service_json,
    validate_route_permission,
)
from tests.conftest import (
    ORGANISATION_ID,
    SERVICE_ONE_ID,
    TEMPLATE_ONE_ID,
    create_active_user_no_api_key_permission,
    create_active_user_no_settings_permission,
    create_active_user_with_permissions,
    create_multiple_email_reply_to_addresses,
    create_multiple_sms_senders,
    create_platform_admin_user,
    create_reply_to_email_address,
    create_sms_sender,
    normalize_spaces,
)

FAKE_TEMPLATE_ID = uuid4()


@pytest.fixture
def _mock_get_service_settings_page_common(
    mock_get_inbound_number_for_service,
    mock_get_free_sms_fragment_limit,
    mock_get_service_data_retention,
    mock_get_organization,
):
    return


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
@pytest.mark.parametrize(
    ("user", "expected_rows"),
    [
        (
            create_active_user_with_permissions(),
            [
                "",
                "Service name Test Service Change service name",
                "Send text messages On",
                "Start text messages with service name On Change your settings "
                "for starting text messages with service name",
            ],
        ),
        (
            create_platform_admin_user(),
            [
                "",
                "Service name Test Service Change service name",
                "Send text messages On",
                "Text message senders (Only visible to Platform Admins) GOVUK Manage text message senders",
                "Start text messages with service name On Change your settings "
                "for starting text messages with service name",
                "Send international text messages Off Change your settings for sending international text messages",
                "Label Value Action",
                "Live Off Change service status",
                "Count in list of live services Yes Change if service is counted in list of live services",
                "Billing details None Change billing details for service",
                "Notes None Change the notes for the service",
                "Organization Test organization Federal government Change organization for service",
                "Rate limit 3,000 per minute Change rate limit",
                "Message batch limit 1,000 per send Change message batch limit",
                "Free text message allowance 250,000 per year Change free text message allowance",
                "Custom data retention Email – 7 days Change data retention",
                "Receive inbound SMS Off Change your settings for Receive inbound SMS",
                "Email authentication Off Change your settings for Email authentication",
            ],
        ),
    ],
)
def test_should_show_overview(
    client_request,
    mocker,
    api_user_active,
    no_reply_to_email_addresses,
    single_sms_sender,
    user,
    expected_rows,
):
    service_one = service_json(
        SERVICE_ONE_ID,
        users=[api_user_active["id"]],
        permissions=["sms", "email"],
        organization_id=ORGANISATION_ID,
        contact_link="contact_us@gsa.gov",
    )
    mocker.patch(
        "app.service_api_client.get_service", return_value={"data": service_one}
    )

    client_request.login(user, service_one)
    page = client_request.get("main.service_settings", service_id=SERVICE_ONE_ID)
    assert page.find("h1").text == "Settings"
    rows = page.select("tr")
    assert len(rows) == len(expected_rows)
    for index, row in enumerate(expected_rows):
        assert row == " ".join(rows[index].text.split())
    app.service_api_client.get_service.assert_called_with(SERVICE_ONE_ID)


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
def test_organization_name_links_to_org_dashboard(
    client_request,
    platform_admin_user,
    no_reply_to_email_addresses,
    single_sms_sender,
    mocker,
):
    service_one = service_json(
        SERVICE_ONE_ID, permissions=["sms", "email"], organization_id=ORGANISATION_ID
    )

    mocker.patch(
        "app.service_api_client.get_service", return_value={"data": service_one}
    )

    client_request.login(platform_admin_user, service_one)
    response = client_request.get("main.service_settings", service_id=SERVICE_ONE_ID)

    org_row = find_element_by_tag_and_partial_text(
        response, tag="tr", string="Organization"
    )
    assert org_row.find("a")["href"] == url_for(
        "main.organization_dashboard", org_id=ORGANISATION_ID
    )
    assert normalize_spaces(org_row.find("a").text) == "Test organization"


@pytest.mark.skip(reason="Email currently deactivated")
@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
@pytest.mark.parametrize(
    ("service_contact_link", "expected_text"),
    [
        (
            "contact.me@gsa.gov",
            "Send files by email contact.me@gsa.gov Manage sending files by email",
        ),
        (None, "Send files by email Not set up Manage sending files by email"),
    ],
)
def test_send_files_by_email_row_on_settings_page(
    client_request,
    platform_admin_user,
    no_reply_to_email_addresses,
    single_sms_sender,
    mocker,
    service_contact_link,
    expected_text,
):
    service_one = service_json(
        SERVICE_ONE_ID,
        permissions=["sms", "email"],
        organization_id=ORGANISATION_ID,
        contact_link=service_contact_link,
    )

    mocker.patch(
        "app.service_api_client.get_service", return_value={"data": service_one}
    )

    client_request.login(platform_admin_user, service_one)
    response = client_request.get("main.service_settings", service_id=SERVICE_ONE_ID)

    org_row = find_element_by_tag_and_partial_text(
        response, tag="tr", string="Send files by email"
    )
    assert normalize_spaces(org_row.get_text()) == expected_text


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
@pytest.mark.parametrize(
    ("permissions", "expected_rows"),
    [
        (
            ["email", "sms", "international_sms"],
            [
                "Service name service one Change service name",
                "Send text messages On",
                "Start text messages with service name On Change your settings "
                "for starting text messages with service name",
            ],
        ),
        (
            ["email", "sms", ServicePermission.EMAIL_AUTH],
            [
                "Service name service one Change service name",
                "Send text messages On",
                "Start text messages with service name On Change your settings "
                "for starting text messages with service name",
            ],
        ),
    ],
)
def test_should_show_overview_for_service_with_more_things_set(
    client_request,
    active_user_with_permissions,
    mocker,
    service_one,
    single_reply_to_email_address,
    single_sms_sender,
    permissions,
    expected_rows,
):
    client_request.login(active_user_with_permissions)
    service_one["permissions"] = permissions
    page = client_request.get("main.service_settings", service_id=service_one["id"])
    for index, row in enumerate(expected_rows):
        assert row == " ".join(page.find_all("tr")[index + 1].text.split())


def test_should_show_service_name(
    client_request,
):
    page = client_request.get("main.service_name_change", service_id=SERVICE_ONE_ID)
    assert page.find("h1").text == "Change your service name"
    assert page.find("input", attrs={"type": "text"})["value"] == "service one"
    assert (
        page.select_one("main .usa-body").text
        == "Your service name should tell users what the message is about as well as who it’s from."
    )

    assert (
        "The service name you enter here will appear at the beginning of each text message, unless"
        in page.text
    )

    app.service_api_client.get_service.assert_called_with(SERVICE_ONE_ID)


def test_should_show_different_change_service_name_page_for_local_services(
    client_request,
    service_one,
    mocker,
):
    mocker.patch(
        "app.organizations_client.get_organization_by_domain",
        return_value=organization_json(organization_type="local"),
    )
    service_one["organization_type"] = "local"
    page = client_request.get("main.service_name_change", service_id=SERVICE_ONE_ID)
    assert page.find("h1").text == "Change your service name"
    assert page.find("input", attrs={"type": "text"})["value"] == "service one"
    assert page.select_one("main .usa-body").text.strip() == (
        "Your service name should tell users what the message is about as well as who it’s from. For example:"
    )
    # when no organization on the service object, default org for the user is used for hint
    assert (
        "School admissions - Test Org"
        in page.find_all("ul", class_="usa-list usa-list--bullet")[0].text
    )

    app.service_api_client.get_service.assert_called_with(SERVICE_ONE_ID)


def test_should_show_service_org_in_hint_on_change_service_name_page_for_local_services_if_service_has_org(
    client_request,
    service_one,
    mocker,
):
    mocker.patch(
        "app.organizations_client.get_organization_by_domain",
        return_value=organization_json(organization_type="local"),
    )
    mocker.patch(
        "app.organizations_client.get_organization",
        return_value=organization_json(
            organization_type="local", name="Local Authority"
        ),
    )
    service_one["organization_type"] = "local"
    service_one["organization"] = "1234"
    page = client_request.get("main.service_name_change", service_id=SERVICE_ONE_ID)
    # when there is organization on the service object, it is used for hint text instead of user default org
    assert (
        "School admissions - Local Authority"
        in page.find_all("ul", class_="usa-list usa-list--bullet")[0].text
    )


def test_should_show_service_name_with_no_prefixing(
    client_request,
    service_one,
):
    service_one["prefix_sms"] = False
    page = client_request.get("main.service_name_change", service_id=SERVICE_ONE_ID)
    assert page.find("h1").text == "Change your service name"
    assert (
        page.select_one("main .usa-body").text
        == "Your service name should tell users what the message is about as well as who it’s from."
    )


@pytest.mark.parametrize(
    ("name", "error_message"),
    [
        ("", "Cannot be empty"),
        (".", "Must include at least two alphanumeric characters"),
        ("a" * 256, "Service name must be 255 characters or fewer"),
    ],
)
def test_service_name_change_fails_if_new_name_fails_validation(
    client_request,
    mock_update_service,
    name,
    error_message,
):
    page = client_request.post(
        "main.service_name_change",
        service_id=SERVICE_ONE_ID,
        _data={"name": name},
        _expected_status=200,
    )
    assert not mock_update_service.called
    assert error_message in page.find("span", {"class": "usa-error-message"}).text


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
@pytest.mark.parametrize(
    ("user", "expected_text", "expected_link"),
    [
        (
            create_active_user_with_permissions(),
            "To remove these restrictions, you can send us a request to go live.",
            True,
        ),
        (
            create_active_user_no_settings_permission(),
            "Your service manager can ask to have these restrictions removed.",
            False,
        ),
    ],
)
def test_show_restricted_service(
    client_request,
    service_one,
    single_reply_to_email_address,
    single_sms_sender,
    user,
    expected_text,
    expected_link,
):
    client_request.login(user)
    page = client_request.get(
        "main.service_settings",
        service_id=SERVICE_ONE_ID,
    )

    assert page.find("h1").text == "Settings"
    assert page.select("main h2")[0].text == "Your service is in trial mode"

    request_to_live = page.select("main p")[1]
    request_to_live_link = request_to_live.select_one("a")
    assert normalize_spaces(request_to_live.text) == expected_text

    if expected_link:
        assert request_to_live_link.text.strip() == "request to go live"
        email_address = "notify-support@gsa.gov"
        assert request_to_live_link["href"] == f"mailto:{email_address}"
    else:
        assert not request_to_live_link


@freeze_time("2017-04-01 11:09:00.061258")
def test_switch_service_to_live(
    client_request,
    platform_admin_user,
    mock_update_service,
    mock_get_inbound_number_for_service,
):
    client_request.login(platform_admin_user)
    client_request.post(
        "main.service_switch_live",
        service_id=SERVICE_ONE_ID,
        _data={"enabled": "True"},
        _expected_status=302,
        _expected_redirect=url_for(
            "main.service_settings",
            service_id=SERVICE_ONE_ID,
        ),
    )
    mock_update_service.assert_called_with(
        SERVICE_ONE_ID,
        message_limit=250000,
        restricted=False,
        go_live_at="2017-04-01 11:09:00.061258",
    )


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
def test_show_live_service(
    client_request,
    mock_get_live_service,
    single_reply_to_email_address,
    single_sms_sender,
):
    page = client_request.get(
        "main.service_settings",
        service_id=SERVICE_ONE_ID,
    )
    assert page.find("h1").text.strip() == "Settings"
    assert "Your service is in trial mode" not in page.text


def test_switch_service_to_restricted(
    client_request,
    platform_admin_user,
    mock_get_live_service,
    mock_update_service,
    mock_get_inbound_number_for_service,
):
    client_request.login(platform_admin_user)
    client_request.post(
        "main.service_switch_live",
        service_id=SERVICE_ONE_ID,
        _data={"enabled": "False"},
        _expected_status=302,
        _expected_response=url_for(
            "main.service_settings",
            service_id=SERVICE_ONE_ID,
        ),
    )
    mock_update_service.assert_called_with(
        SERVICE_ONE_ID, message_limit=50, restricted=True, go_live_at=None
    )


@pytest.mark.parametrize(
    ("count_as_live", "selected", "labelled"),
    [
        (True, "True", "Yes"),
        (False, "False", "No"),
    ],
)
def test_show_switch_service_to_count_as_live_page(
    mocker,
    client_request,
    platform_admin_user,
    mock_update_service,
    count_as_live,
    selected,
    labelled,
):
    mocker.patch(
        "app.models.service.Service.count_as_live",
        create=True,
        new_callable=PropertyMock,
        return_value=count_as_live,
    )
    client_request.login(platform_admin_user)
    page = client_request.get(
        "main.service_switch_count_as_live",
        service_id=SERVICE_ONE_ID,
    )

    client_request.login(platform_admin_user)
    page = client_request.get(
        "main.service_switch_count_as_live",
        service_id=SERVICE_ONE_ID,
    )

    # Find the checked radio button
    checked_input = page.select_one("[checked]")

    # Ensure we actually found a checked input
    assert checked_input is not None, "No checked radio button found"

    # Check that the selected value is as expected
    assert checked_input["value"] == selected

    # Find all labels
    labels = page.select("label.usa-radio__label")

    # Extract label text and see if it matches the expected label
    label_texts = [label.text.strip() for label in labels]

    assert (
        labelled in label_texts
    ), f"Expected label '{labelled}' not found. Found labels: {label_texts}"


@pytest.mark.parametrize(
    ("post_data", "expected_persisted_value"),
    [
        ("True", True),
        ("False", False),
    ],
)
def test_switch_service_to_count_as_live(
    client_request,
    platform_admin_user,
    mock_update_service,
    post_data,
    expected_persisted_value,
):
    client_request.login(platform_admin_user)
    client_request.post(
        "main.service_switch_count_as_live",
        service_id=SERVICE_ONE_ID,
        _data={"enabled": post_data},
        _expected_status=302,
        _expected_redirect=url_for(
            "main.service_settings",
            service_id=SERVICE_ONE_ID,
        ),
    )
    mock_update_service.assert_called_with(
        SERVICE_ONE_ID,
        count_as_live=expected_persisted_value,
    )


def test_should_not_allow_duplicate_service_names(
    client_request,
    mock_update_service_raise_httperror_duplicate_name,
    service_one,
):
    page = client_request.post(
        "main.service_name_change",
        service_id=SERVICE_ONE_ID,
        _data={"name": "SErvICE TWO"},
        _expected_status=200,
    )

    assert "This service name is already in use" in page.text


def test_should_redirect_after_service_name_change(
    client_request,
    mock_update_service,
):
    client_request.post(
        "main.service_name_change",
        service_id=SERVICE_ONE_ID,
        _data={"name": "New Name"},
        _expected_status=302,
        _expected_redirect=url_for(
            "main.service_settings",
            service_id=SERVICE_ONE_ID,
        ),
    )

    mock_update_service.assert_called_once_with(
        SERVICE_ONE_ID,
        name="New Name",
        email_from="new.name",
    )


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
@pytest.mark.parametrize(
    "route",
    [
        "main.service_settings",
        "main.service_name_change",
        "main.archive_service",
    ],
)
def test_route_permissions(
    mocker,
    notify_admin,
    client_request,
    api_user_active,
    service_one,
    single_reply_to_email_address,
    mock_get_invites_for_service,
    single_sms_sender,
    route,
    mock_get_service_templates,
):
    validate_route_permission(
        mocker,
        notify_admin,
        "GET",
        200,
        url_for(route, service_id=service_one["id"]),
        ["manage_service"],
        api_user_active,
        service_one,
        session={"service_name_change": "New Service Name"},
    )


@pytest.mark.parametrize(
    "route",
    [
        "main.service_settings",
        "main.service_name_change",
        "main.service_switch_live",
        "main.archive_service",
    ],
)
def test_route_invalid_permissions(
    mocker,
    notify_admin,
    client_request,
    api_user_active,
    service_one,
    route,
    mock_get_service_templates,
    mock_get_invites_for_service,
):
    validate_route_permission(
        mocker,
        notify_admin,
        "GET",
        403,
        url_for(route, service_id=service_one["id"]),
        ["blah"],
        api_user_active,
        service_one,
    )


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
@pytest.mark.parametrize(
    "route",
    [
        "main.service_settings",
        "main.service_name_change",
    ],
)
def test_route_for_platform_admin(
    mocker,
    notify_admin,
    client_request,
    platform_admin_user,
    service_one,
    single_reply_to_email_address,
    single_sms_sender,
    route,
    mock_get_service_templates,
    mock_get_invites_for_service,
):
    validate_route_permission(
        mocker,
        notify_admin,
        "GET",
        200,
        url_for(route, service_id=service_one["id"]),
        [],
        platform_admin_user,
        service_one,
        session={"service_name_change": "New Service Name"},
    )


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
@pytest.mark.skip(reason="Email currently deactivated")
def test_and_more_hint_appears_on_settings_with_more_than_just_a_single_sender(
    client_request, service_one, multiple_reply_to_email_addresses, multiple_sms_senders
):
    service_one["permissions"] = ["email", "sms"]

    page = client_request.get("main.service_settings", service_id=service_one["id"])

    def get_row(page, label):
        return normalize_spaces(
            find_element_by_tag_and_partial_text(page, tag="tr", string=label).text
        )

    assert (
        get_row(page, "Reply-to email addresses")
        == "Reply-to email addresses test@example.com …and 2 more Manage reply-to email addresses"
    )
    assert (
        get_row(page, "Text message senders")
        == "Text message senders Example …and 2 more Manage text message senders"
    )


@pytest.mark.parametrize(
    ("sender_list_page", "index", "expected_output"),
    [
        (
            "main.service_email_reply_to",
            0,
            "test@example.com (default) Change test@example.com",
        ),
        ("main.service_sms_senders", 0, "GOVUK (default) Change GOVUK"),
    ],
)
def test_api_ids_dont_show_on_option_pages_with_a_single_sender(
    client_request,
    single_reply_to_email_address,
    mock_get_organization,
    single_sms_sender,
    sender_list_page,
    index,
    expected_output,
):
    rows = client_request.get(sender_list_page, service_id=SERVICE_ONE_ID).select(
        ".user-list-item"
    )

    assert normalize_spaces(rows[index].text) == expected_output
    assert len(rows) == index + 1


@pytest.mark.parametrize(
    ("sender_list_page", "endpoint_to_mock", "sample_data", "expected_items"),
    [
        (
            "main.service_email_reply_to",
            "app.service_api_client.get_reply_to_email_addresses",
            create_multiple_email_reply_to_addresses(),
            [
                "test@example.com (default) Change test@example.com ID: 1234",
                "test2@example.com Change test2@example.com ID: 5678",
                "test3@example.com Change test3@example.com ID: 9457",
            ],
        ),
        (
            "main.service_sms_senders",
            "app.service_api_client.get_sms_senders",
            create_multiple_sms_senders(),
            [
                "Example (default and receives replies) Change Example ID: 1234",
                "Example 2 Change Example 2 ID: 5678",
                "US Notify Change US Notify ID: 9457",
                "Notify.gov Change Notify.gov ID: 9897",
            ],
        ),
    ],
)
def test_default_option_shows_for_default_sender(
    client_request,
    mocker,
    sender_list_page,
    endpoint_to_mock,
    sample_data,
    expected_items,
):
    mocker.patch(endpoint_to_mock, return_value=sample_data)

    rows = client_request.get(sender_list_page, service_id=SERVICE_ONE_ID).select(
        ".user-list-item"
    )

    assert [normalize_spaces(row.text) for row in rows] == expected_items


@pytest.mark.parametrize(
    ("sender_list_page", "endpoint_to_mock", "expected_output"),
    [
        (
            "main.service_email_reply_to",
            "app.service_api_client.get_reply_to_email_addresses",
            "You have not added any reply-to email addresses yet",
        ),
        (
            "main.service_sms_senders",
            "app.service_api_client.get_sms_senders",
            "You have not added any text message senders yet",
        ),
    ],
)
def test_no_senders_message_shows(
    client_request, sender_list_page, endpoint_to_mock, expected_output, mocker
):
    mocker.patch(endpoint_to_mock, return_value=[])

    rows = client_request.get(sender_list_page, service_id=SERVICE_ONE_ID).select(
        ".user-list-item"
    )

    assert normalize_spaces(rows[0].text) == expected_output
    assert len(rows) == 1


@pytest.mark.parametrize(
    ("reply_to_input", "expected_error"),
    [
        ("", "Cannot be empty"),
        ("testtest", "Enter a valid email address"),
    ],
)
def test_incorrect_reply_to_email_address_input(
    reply_to_input, expected_error, client_request, no_reply_to_email_addresses
):
    page = client_request.post(
        "main.service_add_email_reply_to",
        service_id=SERVICE_ONE_ID,
        _data={"email_address": reply_to_input},
        _expected_status=200,
    )

    assert expected_error in normalize_spaces(
        page.select_one(".usa-error-message").text
    )


@pytest.mark.parametrize(
    ("sms_sender_input", "expected_error"),
    [
        ("elevenchars", None),
        ("11 chars", None),
        ("", "Cannot be empty"),
        ("abcdefghijkhgkg", "Enter 11 characters or fewer"),
        (r" ¯\_(ツ)_/¯ ", "Use letters and numbers only"),
        ("blood.co.uk", None),
        ("00123", "Cannot start with 00"),
    ],
)
def test_incorrect_sms_sender_input(
    sms_sender_input,
    expected_error,
    client_request,
    no_sms_senders,
    mock_add_sms_sender,
):
    page = client_request.post(
        "main.service_add_sms_sender",
        service_id=SERVICE_ONE_ID,
        _data={"sms_sender": sms_sender_input},
        _expected_status=(200 if expected_error else 302),
    )

    error_message = page.select_one(".usa-error-message")
    count_of_api_calls = len(mock_add_sms_sender.call_args_list)

    if not expected_error:
        assert not error_message
        assert count_of_api_calls == 1
    else:
        assert expected_error in error_message.text
        assert count_of_api_calls == 0


def test_incorrect_sms_sender_input_with_multiple_errors_only_shows_the_first(
    client_request,
    no_sms_senders,
    mock_add_sms_sender,
):
    # There are two errors with the SMS sender - the length and characters used. Only one
    # should be displayed on the page.
    page = client_request.post(
        "main.service_add_sms_sender",
        service_id=SERVICE_ONE_ID,
        _data={"sms_sender": "{}"},
        _expected_status=200,
    )

    error_message = page.select_one(".usa-error-message")
    count_of_api_calls = len(mock_add_sms_sender.call_args_list)

    assert normalize_spaces(error_message.text) == "Error: Enter 3 characters or more"
    assert count_of_api_calls == 0


@pytest.mark.parametrize(
    ("reply_to_addresses", "data", "api_default_args"),
    [
        ([], {}, True),
        (create_multiple_email_reply_to_addresses(), {}, False),
        (create_multiple_email_reply_to_addresses(), {"is_default": "y"}, True),
    ],
)
def test_add_reply_to_email_address_sends_test_notification(
    mocker, client_request, reply_to_addresses, data, api_default_args
):
    mocker.patch(
        "app.service_api_client.get_reply_to_email_addresses",
        return_value=reply_to_addresses,
    )
    data["email_address"] = "test@example.com"
    mock_verify = mocker.patch(
        "app.service_api_client.verify_reply_to_email_address",
        return_value={"data": {"id": "123"}},
    )
    client_request.post(
        "main.service_add_email_reply_to",
        service_id=SERVICE_ONE_ID,
        _data=data,
        _expected_status=302,
        _expected_redirect=url_for(
            "main.service_verify_reply_to_address",
            service_id=SERVICE_ONE_ID,
            notification_id="123",
        )
        + "?is_default={}".format(api_default_args),
    )
    mock_verify.assert_called_once_with(SERVICE_ONE_ID, "test@example.com")


def test_service_add_reply_to_email_address_without_verification_for_platform_admin(
    mocker, client_request, platform_admin_user
):
    client_request.login(platform_admin_user)

    mock_update = mocker.patch("app.service_api_client.add_reply_to_email_address")
    mocker.patch(
        "app.service_api_client.get_reply_to_email_addresses",
        return_value=[create_reply_to_email_address(is_default=True)],
    )
    data = {"is_default": "y", "email_address": "test@example.gsa.gov"}

    client_request.post(
        "main.service_add_email_reply_to",
        service_id=SERVICE_ONE_ID,
        _data=data,
        _expected_status=302,
        _expected_redirect=url_for(
            "main.service_email_reply_to",
            service_id=SERVICE_ONE_ID,
        ),
    )
    mock_update.assert_called_once_with(
        SERVICE_ONE_ID, email_address="test@example.gsa.gov", is_default=True
    )


@pytest.mark.parametrize(
    ("is_default", "replace", "expected_header"),
    [(True, "&replace=123", "Change"), (False, "", "Add")],
)
@pytest.mark.parametrize(
    ("status", "expected_failure", "expected_success"),
    [
        ("delivered", 0, 1),
        ("sending", 0, 0),
        ("permanent-failure", 1, 0),
    ],
)
@freeze_time("2018-06-01 11:11:00.061258")
def test_service_verify_reply_to_address(
    mocker,
    client_request,
    fake_uuid,
    get_non_default_reply_to_email_address,
    status,
    expected_failure,
    expected_success,
    is_default,
    replace,
    expected_header,
):
    notification = {
        "id": fake_uuid,
        "status": status,
        "to": "email@example.gsa.gov",
        "service_id": SERVICE_ONE_ID,
        "template_id": TEMPLATE_ONE_ID,
        "notification_type": "email",
        "created_at": "2018-06-01T11:10:52.499230+00:00",
    }
    mocker.patch(
        "app.notification_api_client.get_notification", return_value=notification
    )
    mock_add_reply_to_email_address = mocker.patch(
        "app.service_api_client.add_reply_to_email_address"
    )
    mock_update_reply_to_email_address = mocker.patch(
        "app.service_api_client.update_reply_to_email_address"
    )
    mocker.patch("app.service_api_client.get_reply_to_email_addresses", return_value=[])
    page = client_request.get(
        "main.service_verify_reply_to_address",
        service_id=SERVICE_ONE_ID,
        notification_id=notification["id"],
        _optional_args="?is_default={}{}".format(is_default, replace),
    )
    assert page.find("h1").text == "{} email reply-to address".format(expected_header)
    if replace:
        assert "/email-reply-to/123/edit" in page.find("a", text="Back").attrs["href"]
    else:
        assert "/email-reply-to/add" in page.find("a", text="Back").attrs["href"]

    assert len(page.find_all("div", class_="banner-dangerous")) == expected_failure
    assert (
        len(page.find_all("div", class_="banner-default-with-tick")) == expected_success
    )

    if status == "delivered":
        if replace:
            mock_update_reply_to_email_address.assert_called_once_with(
                SERVICE_ONE_ID,
                "123",
                email_address=notification["to"],
                is_default=is_default,
            )
            assert mock_add_reply_to_email_address.called is False
        else:
            mock_add_reply_to_email_address.assert_called_once_with(
                SERVICE_ONE_ID, email_address=notification["to"], is_default=is_default
            )
            assert mock_update_reply_to_email_address.called is False
    else:
        assert mock_add_reply_to_email_address.called is False
    if status == "permanent-failure":
        assert page.find("input", type="email").attrs["value"] == notification["to"]


@freeze_time("2018-06-01 11:11:00.061258")
def test_add_reply_to_email_address_fails_if_notification_not_delivered_in_45_sec(
    mocker, client_request, fake_uuid
):
    notification = {
        "id": fake_uuid,
        "status": "sending",
        "to": "email@example.gsa.gov",
        "service_id": SERVICE_ONE_ID,
        "template_id": TEMPLATE_ONE_ID,
        "notification_type": "email",
        "created_at": "2018-06-01T11:10:12.499230+00:00",
    }
    mocker.patch("app.service_api_client.get_reply_to_email_addresses", return_value=[])
    mocker.patch(
        "app.notification_api_client.get_notification", return_value=notification
    )
    mock_add_reply_to_email_address = mocker.patch(
        "app.service_api_client.add_reply_to_email_address"
    )
    page = client_request.get(
        "main.service_verify_reply_to_address",
        service_id=SERVICE_ONE_ID,
        notification_id=notification["id"],
        _optional_args="?is_default={}".format(False),
    )
    expected_banner = page.find_all("div", class_="banner-dangerous")[0]
    assert (
        "There’s a problem with your reply-to address" in expected_banner.text.strip()
    )
    assert mock_add_reply_to_email_address.called is False


@pytest.mark.parametrize(
    ("sms_senders", "data", "api_default_args"),
    [
        ([], {}, True),
        (create_multiple_sms_senders(), {}, False),
        (create_multiple_sms_senders(), {"is_default": "y"}, True),
    ],
)
def test_add_sms_sender(
    sms_senders, data, api_default_args, mocker, client_request, mock_add_sms_sender
):
    mocker.patch("app.service_api_client.get_sms_senders", return_value=sms_senders)
    data["sms_sender"] = "Example"
    client_request.post(
        "main.service_add_sms_sender", service_id=SERVICE_ONE_ID, _data=data
    )

    mock_add_sms_sender.assert_called_once_with(
        SERVICE_ONE_ID, sms_sender="Example", is_default=api_default_args
    )


@pytest.mark.parametrize(
    ("reply_to_addresses", "checkbox_present"),
    [
        ([], False),
        (create_multiple_email_reply_to_addresses(), True),
    ],
)
def test_default_box_doesnt_show_on_first_email_sender(
    reply_to_addresses, mocker, checkbox_present, client_request
):
    mocker.patch(
        "app.service_api_client.get_reply_to_email_addresses",
        return_value=reply_to_addresses,
    )

    page = client_request.get(
        "main.service_add_email_reply_to", service_id=SERVICE_ONE_ID
    )

    assert bool(page.select_one("[name=is_default]")) == checkbox_present


@pytest.mark.parametrize(
    ("reply_to_address", "data", "api_default_args"),
    [
        (create_reply_to_email_address(is_default=True), {"is_default": "y"}, True),
        (create_reply_to_email_address(is_default=True), {}, True),
        (create_reply_to_email_address(is_default=False), {}, False),
        (create_reply_to_email_address(is_default=False), {"is_default": "y"}, True),
    ],
)
def test_edit_reply_to_email_address_sends_verification_notification_if_address_is_changed(
    reply_to_address,
    data,
    api_default_args,
    mocker,
    fake_uuid,
    client_request,
):
    mock_verify = mocker.patch(
        "app.service_api_client.verify_reply_to_email_address",
        return_value={"data": {"id": "123"}},
    )
    mocker.patch(
        "app.service_api_client.get_reply_to_email_address",
        return_value=reply_to_address,
    )
    data["email_address"] = "test@example.gsa.gov"
    client_request.post(
        "main.service_edit_email_reply_to",
        service_id=SERVICE_ONE_ID,
        reply_to_email_id=fake_uuid,
        _data=data,
    )
    mock_verify.assert_called_once_with(SERVICE_ONE_ID, "test@example.gsa.gov")


def test_service_edit_email_reply_to_updates_email_address_without_verification_for_platform_admin(
    mocker, fake_uuid, client_request, platform_admin_user
):
    client_request.login(platform_admin_user)

    mock_update = mocker.patch("app.service_api_client.update_reply_to_email_address")
    mocker.patch(
        "app.service_api_client.get_reply_to_email_address",
        return_value=create_reply_to_email_address(is_default=True),
    )
    data = {"is_default": "y", "email_address": "test@example.gsa.gov"}

    client_request.post(
        "main.service_edit_email_reply_to",
        service_id=SERVICE_ONE_ID,
        reply_to_email_id=fake_uuid,
        _data=data,
        _expected_status=302,
        _expected_redirect=url_for(
            "main.service_email_reply_to",
            service_id=SERVICE_ONE_ID,
        ),
    )
    mock_update.assert_called_once_with(
        SERVICE_ONE_ID,
        reply_to_email_id=fake_uuid,
        email_address="test@example.gsa.gov",
        is_default=True,
    )


@pytest.mark.parametrize(
    ("reply_to_address", "data", "api_default_args"),
    [
        (create_reply_to_email_address(), {"is_default": "y"}, True),
        (create_reply_to_email_address(), {}, True),
        (create_reply_to_email_address(is_default=False), {}, False),
        (create_reply_to_email_address(is_default=False), {"is_default": "y"}, True),
    ],
)
def test_edit_reply_to_email_address_goes_straight_to_update_if_address_not_changed(
    reply_to_address,
    data,
    api_default_args,
    mocker,
    fake_uuid,
    client_request,
    mock_update_reply_to_email_address,
):
    mocker.patch(
        "app.service_api_client.get_reply_to_email_address",
        return_value=reply_to_address,
    )
    mock_verify = mocker.patch("app.service_api_client.verify_reply_to_email_address")
    data["email_address"] = "test@example.com"
    client_request.post(
        "main.service_edit_email_reply_to",
        service_id=SERVICE_ONE_ID,
        reply_to_email_id=fake_uuid,
        _data=data,
    )

    mock_update_reply_to_email_address.assert_called_once_with(
        SERVICE_ONE_ID,
        reply_to_email_id=fake_uuid,
        email_address="test@example.com",
        is_default=api_default_args,
    )
    assert mock_verify.called is False


@pytest.mark.parametrize(
    "url",
    [
        "main.service_edit_email_reply_to",
        "main.service_add_email_reply_to",
    ],
)
def test_add_edit_reply_to_email_address_goes_straight_to_update_if_address_not_changed(
    mocker, fake_uuid, client_request, mock_update_reply_to_email_address, url
):
    reply_to_email_address = create_reply_to_email_address()
    mocker.patch(
        "app.service_api_client.get_reply_to_email_addresses",
        return_value=[reply_to_email_address],
    )
    mocker.patch(
        "app.service_api_client.get_reply_to_email_address",
        return_value=reply_to_email_address,
    )
    error_message = (
        "Your service already uses ‘reply_to@example.com’ as an email reply-to address."
    )
    mocker.patch(
        "app.service_api_client.verify_reply_to_email_address",
        side_effect=[
            HTTPError(
                response=Mock(
                    status_code=409, json={"result": "error", "message": error_message}
                ),
                message=error_message,
            )
        ],
    )
    data = {"is_default": "y", "email_address": "reply_to@example.com"}
    page = client_request.post(
        url,
        service_id=SERVICE_ONE_ID,
        reply_to_email_id=fake_uuid,
        _data=data,
        _follow_redirects=True,
    )

    assert page.find("h1").text == "Reply-to email addresses"
    assert error_message in page.find("div", class_="banner-dangerous").text

    assert mock_update_reply_to_email_address.called is False


@pytest.mark.parametrize(
    ("reply_to_address", "default_choice_and_delete_link_expected"),
    [
        (
            create_reply_to_email_address(is_default=False),
            True,
        ),
        (
            create_reply_to_email_address(is_default=True),
            False,
        ),
    ],
)
def test_shows_delete_link_for_get_request_for_edit_email_reply_to_address(
    mocker,
    reply_to_address,
    default_choice_and_delete_link_expected,
    fake_uuid,
    client_request,
):
    mocker.patch(
        "app.service_api_client.get_reply_to_email_address",
        return_value=reply_to_address,
    )

    page = client_request.get(
        "main.service_edit_email_reply_to",
        service_id=SERVICE_ONE_ID,
        reply_to_email_id=sample_uuid(),
    )

    assert page.select_one(".usa-back-link").text.strip() == "Back"
    assert page.select_one(".usa-back-link")["href"] == url_for(
        ".service_email_reply_to",
        service_id=SERVICE_ONE_ID,
    )

    if default_choice_and_delete_link_expected:
        link = page.select_one(".page-footer a")
        assert normalize_spaces(link.text) == "Delete"
        assert link["href"] == url_for(
            "main.service_confirm_delete_email_reply_to",
            service_id=SERVICE_ONE_ID,
            reply_to_email_id=sample_uuid(),
        )
        assert not page.select_one("input#is_default").has_attr("checked")

    else:
        assert not page.select(".page-footer a")


@pytest.mark.parametrize(
    (
        "reply_to_address",
        "default_choice_and_delete_link_expected",
        "default_checkbox_checked",
    ),
    [
        (create_reply_to_email_address(is_default=False), True, False),
        (create_reply_to_email_address(is_default=False), True, True),
        (
            create_reply_to_email_address(is_default=True),
            False,
            False,  # not expecting a checkbox to even be shown to be ticked
        ),
    ],
)
def test_shows_delete_link_for_error_on_post_request_for_edit_email_reply_to_address(
    mocker,
    reply_to_address,
    default_choice_and_delete_link_expected,
    default_checkbox_checked,
    fake_uuid,
    client_request,
):
    mocker.patch(
        "app.service_api_client.get_reply_to_email_address",
        return_value=reply_to_address,
    )

    data = {"email_address": "not a valid email address"}
    if default_checkbox_checked:
        data["is_default"] = "y"

    page = client_request.post(
        "main.service_edit_email_reply_to",
        service_id=SERVICE_ONE_ID,
        reply_to_email_id=sample_uuid(),
        _data=data,
        _expected_status=200,
    )

    assert page.select_one(".usa-back-link").text.strip() == "Back"
    assert page.select_one(".usa-back-link")["href"] == url_for(
        ".service_email_reply_to",
        service_id=SERVICE_ONE_ID,
    )
    assert (
        page.select_one(".usa-error-message").text.strip()
        == "Error: Enter a valid email address"
    )

    assert page.select_one("input[name='email_address']")

    if default_choice_and_delete_link_expected:
        link = page.select_one(".page-footer a")
        assert normalize_spaces(link.text) == "Delete"
        assert link["href"] == url_for(
            "main.service_confirm_delete_email_reply_to",
            service_id=SERVICE_ONE_ID,
            reply_to_email_id=sample_uuid(),
        )
        assert (
            page.select_one("input#is_default").has_attr("checked")
            == default_checkbox_checked
        )
    else:
        assert not page.select(".page-footer a")


def test_confirm_delete_reply_to_email_address(
    fake_uuid, client_request, get_non_default_reply_to_email_address
):
    page = client_request.get(
        "main.service_confirm_delete_email_reply_to",
        service_id=SERVICE_ONE_ID,
        reply_to_email_id=fake_uuid,
        _test_page_title=False,
    )

    assert normalize_spaces(page.select_one(".banner-dangerous").text) == (
        "Are you sure you want to delete this reply-to email address? " "Yes, delete"
    )
    assert "action" not in page.select_one(".banner-dangerous form")
    assert page.select_one(".banner-dangerous form")["method"] == "post"


def test_delete_reply_to_email_address(
    client_request,
    service_one,
    fake_uuid,
    get_non_default_reply_to_email_address,
    mocker,
):
    mock_delete = mocker.patch("app.service_api_client.delete_reply_to_email_address")
    client_request.post(
        ".service_delete_email_reply_to",
        service_id=SERVICE_ONE_ID,
        reply_to_email_id=fake_uuid,
        _expected_redirect=url_for(
            "main.service_email_reply_to",
            service_id=SERVICE_ONE_ID,
        ),
    )
    mock_delete.assert_called_once_with(
        service_id=SERVICE_ONE_ID, reply_to_email_id=fake_uuid
    )


@pytest.mark.parametrize(
    ("sms_sender", "data", "api_default_args"),
    [
        (create_sms_sender(), {"is_default": "y", "sms_sender": "test"}, True),
        (create_sms_sender(), {"sms_sender": "test"}, True),
        (create_sms_sender(is_default=False), {"sms_sender": "test"}, False),
        (
            create_sms_sender(is_default=False),
            {"is_default": "y", "sms_sender": "test"},
            True,
        ),
    ],
)
def test_edit_sms_sender(
    sms_sender,
    data,
    api_default_args,
    mocker,
    fake_uuid,
    client_request,
    mock_update_sms_sender,
):
    mocker.patch("app.service_api_client.get_sms_sender", return_value=sms_sender)

    client_request.post(
        "main.service_edit_sms_sender",
        service_id=SERVICE_ONE_ID,
        sms_sender_id=fake_uuid,
        _data=data,
    )

    mock_update_sms_sender.assert_called_once_with(
        SERVICE_ONE_ID,
        sms_sender_id=fake_uuid,
        sms_sender="test",
        is_default=api_default_args,
    )


@pytest.mark.parametrize(
    (
        "sender_page",
        "endpoint_to_mock",
        "sender_details",
        "default_message",
        "params",
        "checkbox_present",
    ),
    [
        (
            "main.service_edit_email_reply_to",
            "app.service_api_client.get_reply_to_email_address",
            create_reply_to_email_address(is_default=True),
            "This is the default reply-to address for service one emails",
            "reply_to_email_id",
            False,
        ),
        (
            "main.service_edit_email_reply_to",
            "app.service_api_client.get_reply_to_email_address",
            create_reply_to_email_address(is_default=False),
            "This is the default reply-to address for service one emails",
            "reply_to_email_id",
            True,
        ),
        (
            "main.service_edit_sms_sender",
            "app.service_api_client.get_sms_sender",
            create_sms_sender(is_default=True),
            "This is the default text message sender.",
            "sms_sender_id",
            False,
        ),
        (
            "main.service_edit_sms_sender",
            "app.service_api_client.get_sms_sender",
            create_sms_sender(is_default=False),
            "This is the default text message sender.",
            "sms_sender_id",
            True,
        ),
    ],
)
def test_default_box_shows_on_non_default_sender_details_while_editing(
    fake_uuid,
    mocker,
    sender_page,
    endpoint_to_mock,
    sender_details,
    client_request,
    default_message,
    checkbox_present,
    params,
):
    page_arguments = {"service_id": SERVICE_ONE_ID}
    page_arguments[params] = fake_uuid

    mocker.patch(endpoint_to_mock, return_value=sender_details)

    page = client_request.get(sender_page, **page_arguments)

    if checkbox_present:
        assert page.select_one("[name=is_default]")
    else:
        assert normalize_spaces(page.select_one("form p").text) == (default_message)


@pytest.mark.parametrize(
    ("sms_sender", "expected_link_text", "partial_href"),
    [
        (
            create_sms_sender(is_default=False),
            "Delete",
            partial(
                url_for,
                "main.service_confirm_delete_sms_sender",
                sms_sender_id=sample_uuid(),
            ),
        ),
        (
            create_sms_sender(is_default=True),
            None,
            None,
        ),
    ],
)
def test_shows_delete_link_for_sms_sender(
    mocker,
    sms_sender,
    expected_link_text,
    partial_href,
    fake_uuid,
    client_request,
):
    mocker.patch("app.service_api_client.get_sms_sender", return_value=sms_sender)

    page = client_request.get(
        "main.service_edit_sms_sender",
        service_id=SERVICE_ONE_ID,
        sms_sender_id=sample_uuid(),
    )

    link = page.select_one(".page-footer a")
    back_link = page.select_one(".usa-back-link")

    assert back_link.text.strip() == "Back"
    assert back_link["href"] == url_for(
        ".service_sms_senders",
        service_id=SERVICE_ONE_ID,
    )

    if expected_link_text:
        assert normalize_spaces(link.text) == expected_link_text
        assert link["href"] == partial_href(service_id=SERVICE_ONE_ID)
    else:
        assert not link


def test_confirm_delete_sms_sender(
    fake_uuid,
    client_request,
    get_non_default_sms_sender,
):
    page = client_request.get(
        "main.service_confirm_delete_sms_sender",
        service_id=SERVICE_ONE_ID,
        sms_sender_id=fake_uuid,
        _test_page_title=False,
    )

    assert normalize_spaces(page.select_one(".banner-dangerous").text) == (
        "Are you sure you want to delete this text message sender? " "Yes, delete"
    )
    assert "action" not in page.select_one(".banner-dangerous form")
    assert page.select_one(".banner-dangerous form")["method"] == "post"


@pytest.mark.parametrize(
    ("sms_sender", "expected_link_text"),
    [
        (create_sms_sender(is_default=False, inbound_number_id="1234"), None),
        (create_sms_sender(is_default=True), None),
        (create_sms_sender(is_default=False), "Delete"),
    ],
)
def test_inbound_sms_sender_is_not_deleteable(
    client_request, service_one, fake_uuid, sms_sender, expected_link_text, mocker
):
    mocker.patch("app.service_api_client.get_sms_sender", return_value=sms_sender)

    page = client_request.get(
        ".service_edit_sms_sender",
        service_id=SERVICE_ONE_ID,
        sms_sender_id=fake_uuid,
    )

    back_link = page.select_one(".usa-back-link")
    footer_link = page.select_one(".page-footer a")
    assert normalize_spaces(back_link.text) == "Back"

    if expected_link_text:
        assert normalize_spaces(footer_link.text) == expected_link_text
    else:
        assert not footer_link


def test_delete_sms_sender(
    client_request,
    service_one,
    fake_uuid,
    get_non_default_sms_sender,
    mocker,
):
    mock_delete = mocker.patch("app.service_api_client.delete_sms_sender")
    client_request.post(
        ".service_delete_sms_sender",
        service_id=SERVICE_ONE_ID,
        sms_sender_id=fake_uuid,
        _expected_redirect=url_for(
            "main.service_sms_senders",
            service_id=SERVICE_ONE_ID,
        ),
    )
    mock_delete.assert_called_once_with(
        service_id=SERVICE_ONE_ID, sms_sender_id=fake_uuid
    )


@pytest.mark.parametrize(
    ("sms_sender", "hide_textbox"),
    [
        (create_sms_sender(is_default=False, inbound_number_id="1234"), True),
        (create_sms_sender(is_default=True), False),
    ],
)
def test_inbound_sms_sender_is_not_editable(
    client_request, service_one, fake_uuid, sms_sender, hide_textbox, mocker
):
    mocker.patch("app.service_api_client.get_sms_sender", return_value=sms_sender)

    page = client_request.get(
        ".service_edit_sms_sender",
        service_id=SERVICE_ONE_ID,
        sms_sender_id=fake_uuid,
    )

    assert bool(page.find("input", attrs={"name": "sms_sender"})) != hide_textbox
    if hide_textbox:
        assert (
            normalize_spaces(page.select_one('form[method="post"] p').text)
            == "GOVUK This phone number receives replies and cannot be changed"
        )


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
def test_shows_research_mode_indicator(
    client_request,
    service_one,
    mocker,
    single_reply_to_email_address,
    single_sms_sender,
):
    service_one["research_mode"] = True
    mocker.patch("app.service_api_client.update_service", return_value=service_one)

    page = client_request.get(
        "main.service_settings",
        service_id=SERVICE_ONE_ID,
    )

    element = page.find("span", {"id": "research-mode"})
    assert element.text == "research mode"


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
def test_does_not_show_research_mode_indicator(
    client_request, single_reply_to_email_address, single_sms_sender
):
    page = client_request.get(
        "main.service_settings",
        service_id=SERVICE_ONE_ID,
    )

    element = page.find("span", {"id": "research-mode"})
    assert not element


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.parametrize(
    "endpoint",
    [
        "main.set_free_sms_allowance",
        "main.set_message_limit",
        "main.set_rate_limit",
    ],
)
def test_organization_type_pages_are_platform_admin_only(
    client_request,
    method,
    endpoint,
):
    getattr(client_request, method)(
        endpoint,
        service_id=SERVICE_ONE_ID,
        _expected_status=403,
        _test_page_title=False,
    )


def test_should_show_page_to_set_sms_allowance(
    client_request, platform_admin_user, mock_get_free_sms_fragment_limit
):
    client_request.login(platform_admin_user)
    page = client_request.get("main.set_free_sms_allowance", service_id=SERVICE_ONE_ID)

    assert (
        normalize_spaces(page.select_one("label").text)
        == "Numbers of text message fragments per year"
    )
    mock_get_free_sms_fragment_limit.assert_called_once_with(SERVICE_ONE_ID)


@freeze_time("2017-04-01 11:09:00.061258")
@pytest.mark.parametrize(
    ("given_allowance", "expected_api_argument"),
    [
        ("0", 0),
        ("1", 1),
        ("250000", 250000),
    ],
)
def test_should_set_sms_allowance(
    client_request,
    platform_admin_user,
    given_allowance,
    expected_api_argument,
    mock_get_free_sms_fragment_limit,
    mock_create_or_update_free_sms_fragment_limit,
):
    client_request.login(platform_admin_user)
    client_request.post(
        "main.set_free_sms_allowance",
        service_id=SERVICE_ONE_ID,
        _data={
            "free_sms_allowance": given_allowance,
        },
        _expected_redirect=url_for(
            "main.service_settings",
            service_id=SERVICE_ONE_ID,
        ),
    )

    mock_create_or_update_free_sms_fragment_limit.assert_called_with(
        SERVICE_ONE_ID, expected_api_argument
    )


@freeze_time("2017-04-01 11:09:00.061258")
@pytest.mark.parametrize(
    ("given_allowance", "expected_api_argument"),
    [
        pytest.param("foo", "foo"),
    ],
)
def test_should_set_sms_allowance_fails(
    client_request,
    platform_admin_user,
    given_allowance,
    expected_api_argument,
    mock_get_free_sms_fragment_limit,
    mock_create_or_update_free_sms_fragment_limit,
):
    client_request.login(platform_admin_user)
    with pytest.raises(expected_exception=AssertionError):
        client_request.post(
            "main.set_free_sms_allowance",
            service_id=SERVICE_ONE_ID,
            _data={
                "free_sms_allowance": given_allowance,
            },
            _expected_redirect=url_for(
                "main.service_settings",
                service_id=SERVICE_ONE_ID,
            ),
        )


def test_should_show_page_to_set_message_limit(
    client_request,
    platform_admin_user,
):
    client_request.login(platform_admin_user)
    page = client_request.get("main.set_message_limit", service_id=SERVICE_ONE_ID)
    assert normalize_spaces(page.select_one("label").text) == (
        "Max number of messages the service has per send"
    )
    assert normalize_spaces(page.select_one("input[type=text]")["value"]) == ("1000")


def test_should_show_page_to_set_rate_limit(
    client_request,
    platform_admin_user,
):
    client_request.login(platform_admin_user)
    page = client_request.get("main.set_rate_limit", service_id=SERVICE_ONE_ID)
    assert normalize_spaces(page.select_one("label").text) == (
        "Number of messages the service can send in a rolling 60 second window"
    )
    assert normalize_spaces(page.select_one("input[type=text]")["value"]) == ("3000")


@pytest.mark.parametrize(
    ("endpoint", "field_name"),
    [
        ("main.set_message_limit", "message_limit"),
        ("main.set_rate_limit", "rate_limit"),
    ],
)
@pytest.mark.parametrize(
    ("new_limit", "expected_api_argument"),
    [
        ("1", 1),
        ("250000", 250000),
        pytest.param("foo", "foo", marks=pytest.mark.xfail),
    ],
)
def test_should_set_message_limit(
    client_request,
    platform_admin_user,
    new_limit,
    expected_api_argument,
    mock_update_service,
    endpoint,
    field_name,
):
    client_request.login(platform_admin_user)
    client_request.post(
        endpoint,
        service_id=SERVICE_ONE_ID,
        _data={
            field_name: new_limit,
        },
    )
    mock_update_service.assert_called_once_with(
        SERVICE_ONE_ID,
        **{field_name: expected_api_argument},
    )


def test_unknown_channel_404s(
    client_request,
):
    client_request.get(
        "main.service_set_channel",
        service_id=SERVICE_ONE_ID,
        channel="message-in-a-bottle",
        _expected_status=404,
    )


@pytest.mark.parametrize(
    (
        "channel",
        "expected_first_para",
        "expected_legend",
        "initial_permissions",
        "expected_initial_value",
        "posted_value",
        "expected_updated_permissions",
    ),
    [
        (
            "sms",
            "You may send up to 250,000 text messages during the pilot period.",
            "Send text messages",
            [],
            "False",
            "True",
            ["sms"],
        ),
        (
            "email",
            "It’s free to send emails through Notify.gov.",
            "Send emails",
            [],
            "False",
            "True",
            ["email"],
        ),
        (
            "email",
            "It’s free to send emails through Notify.gov.",
            "Send emails",
            ["email", "sms"],
            "True",
            "True",
            ["email", "sms"],
        ),
    ],
)
def test_switch_service_channels_on_and_off(
    client_request,
    service_one,
    mocker,
    mock_get_free_sms_fragment_limit,
    channel,
    expected_first_para,
    expected_legend,
    initial_permissions,
    expected_initial_value,
    posted_value,
    expected_updated_permissions,
):
    mocked_fn = mocker.patch(
        "app.service_api_client.update_service", return_value=service_one
    )
    service_one["permissions"] = initial_permissions

    page = client_request.get(
        "main.service_set_channel",
        service_id=service_one["id"],
        channel=channel,
    )

    assert normalize_spaces(page.select_one("main p").text) == expected_first_para
    assert normalize_spaces(page.select_one("legend").text) == expected_legend

    assert page.select_one("input[checked]")["value"] == expected_initial_value
    assert len(page.select("input[checked]")) == 1

    client_request.post(
        "main.service_set_channel",
        service_id=service_one["id"],
        channel=channel,
        _data={"enabled": posted_value},
        _expected_redirect=url_for(
            "main.service_settings",
            service_id=service_one["id"],
        ),
    )
    assert set(mocked_fn.call_args[1]["permissions"]) == set(
        expected_updated_permissions
    )
    assert mocked_fn.call_args[0][0] == service_one["id"]


@pytest.mark.parametrize(
    ("permission", "permissions", "expected_checked"),
    [
        ("international_sms", ["international_sms"], "True"),
        ("international_sms", [""], "False"),
    ],
)
def test_show_international_sms_as_radio_button(
    client_request,
    service_one,
    mocker,
    permission,
    permissions,
    expected_checked,
):
    service_one["permissions"] = permissions

    checked_radios = client_request.get(
        f"main.service_set_{permission}",
        service_id=service_one["id"],
    ).select(".usa-radio input[checked]")

    assert len(checked_radios) == 1
    assert checked_radios[0]["value"] == expected_checked


@pytest.mark.parametrize("permission", ["international_sms"])
@pytest.mark.parametrize(
    ("post_value", "permission_expected_in_api_call"),
    [
        ("True", True),
        ("False", False),
    ],
)
def test_switch_service_enable_international_sms(
    client_request,
    service_one,
    mocker,
    permission,
    post_value,
    permission_expected_in_api_call,
):
    mocked_fn = mocker.patch(
        "app.service_api_client.update_service", return_value=service_one
    )
    client_request.post(
        f"main.service_set_{permission}",
        service_id=service_one["id"],
        _data={"enabled": post_value},
        _expected_redirect=url_for(
            "main.service_settings", service_id=service_one["id"]
        ),
    )

    if permission_expected_in_api_call:
        assert permission in mocked_fn.call_args[1]["permissions"]
    else:
        assert permission not in mocked_fn.call_args[1]["permissions"]

    assert mocked_fn.call_args[0][0] == service_one["id"]


@pytest.mark.parametrize(
    ("user", "is_trial_service"),
    [
        (create_platform_admin_user(), True),
        (create_platform_admin_user(), False),
        (create_active_user_with_permissions(), True),
    ],
)
def test_archive_service_after_confirm(
    client_request,
    mocker,
    mock_get_organizations,
    mock_get_service_and_organization_counts,
    mock_get_organizations_and_services_for_user,
    mock_get_users_by_service,
    mock_get_service_templates,
    service_one,
    user,
    is_trial_service,
):
    service_one["restricted"] = is_trial_service
    mock_api = mocker.patch("app.service_api_client.post")
    mock_event = mocker.patch(
        "app.main.views.service_settings.create_archive_service_event"
    )
    redis_delete_mock = mocker.patch(
        "app.notify_client.service_api_client.redis_client.delete"
    )
    mocker.patch("app.notify_client.service_api_client.redis_client.delete_by_pattern")

    client_request.login(user)
    page = client_request.post(
        "main.archive_service",
        service_id=SERVICE_ONE_ID,
        _follow_redirects=True,
    )

    mock_api.assert_called_once_with(
        "/service/{}/archive".format(SERVICE_ONE_ID), data=None
    )
    mock_event.assert_called_once_with(
        service_id=SERVICE_ONE_ID, archived_by_id=user["id"]
    )

    assert normalize_spaces(page.select_one("h1").text) == "Choose service"
    assert normalize_spaces(page.select_one(".banner-default-with-tick").text) == (
        "‘service one’ was deleted"
    )
    # The one user which is part of this service has the sample_uuid as it's user ID
    assert call(f"user-{sample_uuid()}") in redis_delete_mock.call_args_list


@pytest.mark.parametrize(
    ("user", "is_trial_service"),
    [
        pytest.param(create_active_user_with_permissions(), False),
        pytest.param(create_active_user_no_settings_permission(), True),
    ],
)
def test_archive_service_after_confirm_error(
    client_request,
    mocker,
    mock_get_organizations,
    mock_get_service_and_organization_counts,
    mock_get_organizations_and_services_for_user,
    mock_get_users_by_service,
    mock_get_service_templates,
    service_one,
    user,
    is_trial_service,
):
    service_one["restricted"] = is_trial_service
    mocker.patch("app.service_api_client.post")
    mocker.patch("app.main.views.service_settings.create_archive_service_event")
    mocker.patch("app.notify_client.service_api_client.redis_client.delete")
    mocker.patch("app.notify_client.service_api_client.redis_client.delete_by_pattern")

    client_request.login(user)
    with pytest.raises(expected_exception=AssertionError):
        client_request.post(
            "main.archive_service",
            service_id=SERVICE_ONE_ID,
            _follow_redirects=True,
        )


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
@pytest.mark.parametrize(
    ("user", "is_trial_service"),
    [
        (create_platform_admin_user(), True),
        (create_platform_admin_user(), False),
        (create_active_user_with_permissions(), True),
    ],
)
def test_archive_service_prompts_user(
    client_request,
    mocker,
    single_reply_to_email_address,
    service_one,
    single_sms_sender,
    user,
    is_trial_service,
):
    mock_api = mocker.patch("app.service_api_client.post")
    service_one["restricted"] = is_trial_service
    client_request.login(user)

    settings_page = client_request.get(
        "main.archive_service", service_id=SERVICE_ONE_ID
    )
    delete_link = settings_page.select(".page-footer-link a")[0]
    assert normalize_spaces(delete_link.text) == "Delete this service"
    assert delete_link["href"] == url_for(
        "main.archive_service",
        service_id=SERVICE_ONE_ID,
    )

    delete_page = client_request.get(
        "main.archive_service",
        service_id=SERVICE_ONE_ID,
    )
    assert normalize_spaces(delete_page.select_one(".banner-dangerous").text) == (
        "Are you sure you want to delete ‘service one’? "
        "There’s no way to undo this. "
        "Yes, delete"
    )
    assert mock_api.called is False


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
@pytest.mark.parametrize(
    ("user", "is_trial_service"),
    [
        pytest.param(create_active_user_with_permissions(), False),
        pytest.param(create_active_user_no_settings_permission(), True),
    ],
)
def test_archive_service_prompts_user_error(
    client_request,
    mocker,
    single_reply_to_email_address,
    service_one,
    single_sms_sender,
    user,
    is_trial_service,
):
    mocker.patch("app.service_api_client.post")
    service_one["restricted"] = is_trial_service
    client_request.login(user)

    with pytest.raises(expected_exception=AssertionError):
        client_request.get("main.archive_service", service_id=SERVICE_ONE_ID)


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
def test_cant_archive_inactive_service(
    client_request,
    platform_admin_user,
    service_one,
    single_reply_to_email_address,
    single_sms_sender,
):
    service_one["active"] = False

    client_request.login(platform_admin_user)
    page = client_request.get(
        "main.service_settings",
        service_id=service_one["id"],
    )

    assert "Delete service" not in {a.text for a in page.find_all("a", class_="button")}


@pytest.mark.parametrize("user", [create_platform_admin_user()])
def test_suspend_service_after_confirm(
    client_request,
    user,
    mocker,
):
    mock_api = mocker.patch("app.service_api_client.post")
    mock_event = mocker.patch(
        "app.main.views.service_settings.create_suspend_service_event"
    )

    client_request.login(user)
    client_request.post(
        "main.suspend_service",
        service_id=SERVICE_ONE_ID,
        _expected_redirect=url_for(
            "main.service_settings",
            service_id=SERVICE_ONE_ID,
        ),
    )

    mock_api.assert_called_once_with(
        "/service/{}/suspend".format(SERVICE_ONE_ID), data=None
    )
    mock_event.assert_called_once_with(
        service_id=SERVICE_ONE_ID, suspended_by_id=user["id"]
    )


@pytest.mark.parametrize("user", [pytest.param(create_active_user_with_permissions())])
def test_suspend_service_after_confirm_error(
    client_request,
    user,
    mocker,
):
    mocker.patch("app.service_api_client.post")
    mocker.patch("app.main.views.service_settings.create_suspend_service_event")
    client_request.login(user)
    with pytest.raises(expected_exception=AssertionError):
        client_request.post(
            "main.suspend_service",
            service_id=SERVICE_ONE_ID,
            _expected_redirect=url_for(
                "main.service_settings",
                service_id=SERVICE_ONE_ID,
            ),
        )


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
@pytest.mark.parametrize(
    "user",
    [
        create_platform_admin_user(),
        pytest.param(create_active_user_with_permissions()),
    ],
)
def test_suspend_service_prompts_user(
    client_request,
    user,
    service_one,
    mocker,
    single_reply_to_email_address,
    single_sms_sender,
):
    mock_api = mocker.patch("app.service_api_client.post")

    client_request.login(user)

    if user["email_address"] != "platform@admin.gsa.gov":
        with pytest.raises(expected_exception=AssertionError):
            client_request.get("main.suspend_service", service_id=service_one["id"])
        return

    page = client_request.get("main.suspend_service", service_id=service_one["id"])

    assert (
        "This will suspend the service and revoke all api keys. Are you sure you want to suspend this service?"
        in page.find("div", class_="banner-dangerous").text
    )
    assert mock_api.called is False


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
def test_cant_suspend_inactive_service(
    client_request,
    platform_admin_user,
    service_one,
    single_reply_to_email_address,
    single_sms_sender,
):
    service_one["active"] = False

    client_request.login(platform_admin_user)
    page = client_request.get(
        "main.service_settings",
        service_id=service_one["id"],
    )

    assert "Suspend service" not in {
        a.text for a in page.find_all("a", class_="button")
    }


@pytest.mark.parametrize(
    "user",
    [
        create_platform_admin_user(),
        create_active_user_with_permissions(),
    ],
)
def test_resume_service_after_confirm(
    mocker,
    user,
    service_one,
    client_request,
):
    service_one["active"] = False
    mock_api = mocker.patch("app.service_api_client.post")
    mock_event = mocker.patch(
        "app.main.views.service_settings.create_resume_service_event"
    )

    client_request.login(user)
    if user["email_address"] != "platform@admin.gsa.gov":
        client_request.post(
            "main.resume_service",
            service_id=SERVICE_ONE_ID,
            _expected_status=403,
        )
        return

    client_request.post(
        "main.resume_service",
        service_id=SERVICE_ONE_ID,
        _expected_redirect=url_for(
            "main.service_settings",
            service_id=SERVICE_ONE_ID,
        ),
    )

    mock_api.assert_called_once_with(f"/service/{SERVICE_ONE_ID}/resume", data=None)
    mock_event.assert_called_once_with(
        service_id=SERVICE_ONE_ID, resumed_by_id=user["id"]
    )


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
@pytest.mark.parametrize(
    "user",
    [
        create_platform_admin_user(),
        pytest.param(create_active_user_with_permissions(), marks=pytest.mark.xfail),
    ],
)
def test_resume_service_prompts_user(
    client_request,
    user,
    service_one,
    single_reply_to_email_address,
    single_sms_sender,
    mocker,
):
    service_one["active"] = False
    mock_api = mocker.patch("app.service_api_client.post")

    client_request.login(user)
    page = client_request.get("main.resume_service", service_id=service_one["id"])

    assert (
        "This will resume the service. New api key are required for this service to use the API."
        in page.find("div", class_="banner-dangerous").text
    )
    assert mock_api.called is False


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
def test_cant_resume_active_service(
    client_request,
    platform_admin_user,
    service_one,
    single_reply_to_email_address,
    single_sms_sender,
):
    client_request.login(platform_admin_user)
    page = client_request.get(
        "main.service_settings",
        service_id=service_one["id"],
    )
    assert "Resume service" not in {a.text for a in page.find_all("a", class_="button")}


@pytest.mark.parametrize(
    ("contact_details_type", "contact_details_value"),
    [
        ("url", "http://example.com/"),
        ("email_address", "me@example.com"),
        ("phone_number", "202 867 5309"),
    ],
)
def test_send_files_by_email_contact_details_prefills_the_form_with_the_existing_contact_details(
    client_request,
    service_one,
    contact_details_type,
    contact_details_value,
):
    service_one["contact_link"] = contact_details_value

    page = client_request.get(
        "main.send_files_by_email_contact_details", service_id=SERVICE_ONE_ID
    )

    assert page.find(
        "input", attrs={"name": "contact_details_type", "value": contact_details_type}
    ).has_attr("checked")

    assert (
        page.find("input", {"name": contact_details_type}).get("value")
        == contact_details_value
    )


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
@pytest.mark.parametrize(
    ("contact_details_type", "old_value", "new_value"),
    [
        ("url", "http://example.com/", "http://new-link.com/"),
        ("email_address", "old@example.com", "new@example.com"),
        ("phone_number", "2021234567", "2028901234"),
    ],
)
def test_send_files_by_email_contact_details_updates_contact_details_and_redirects_to_settings_page(
    client_request,
    service_one,
    mock_update_service,
    no_reply_to_email_addresses,
    single_sms_sender,
    contact_details_type,
    old_value,
    new_value,
):
    service_one["contact_link"] = old_value

    page = client_request.post(
        "main.send_files_by_email_contact_details",
        service_id=SERVICE_ONE_ID,
        _data={
            "contact_details_type": contact_details_type,
            contact_details_type: new_value,
        },
        _follow_redirects=True,
    )

    assert page.h1.text == "Settings"
    mock_update_service.assert_called_once_with(SERVICE_ONE_ID, contact_link=new_value)


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
def test_send_files_by_email_contact_details_uses_the_selected_field_when_multiple_textboxes_contain_data(
    client_request,
    service_one,
    mock_update_service,
    no_reply_to_email_addresses,
    single_sms_sender,
):
    service_one["contact_link"] = "http://www.old-url.com"

    page = client_request.post(
        "main.send_files_by_email_contact_details",
        service_id=SERVICE_ONE_ID,
        _data={
            "contact_details_type": "url",
            "url": "http://www.new-url.com",
            "email_address": "me@example.com",
            "phone_number": "202 867 5309",
        },
        _follow_redirects=True,
    )

    assert page.h1.text == "Settings"
    mock_update_service.assert_called_once_with(
        SERVICE_ONE_ID, contact_link="http://www.new-url.com"
    )


@pytest.mark.parametrize(
    ("contact_link", "subheader", "button_selected"),
    [
        (
            "contact.me@gsa.gov",
            "Change contact details for the file download page",
            True,
        ),
        (None, "Add contact details to the file download page", False),
    ],
)
def test_send_files_by_email_contact_details_page(
    client_request,
    service_one,
    active_user_with_permissions,
    contact_link,
    subheader,
    button_selected,
):
    service_one["contact_link"] = contact_link
    page = client_request.get(
        "main.send_files_by_email_contact_details", service_id=SERVICE_ONE_ID
    )
    assert normalize_spaces(page.find_all("h2")[0].text) == subheader
    if button_selected:
        assert (
            "checked"
            in page.find(
                "input", {"name": "contact_details_type", "value": "email_address"}
            ).attrs
        )
    else:
        assert (
            "checked"
            not in page.find(
                "input", {"name": "contact_details_type", "value": "email_address"}
            ).attrs
        )


def test_send_files_by_email_contact_details_displays_error_message_when_no_radio_button_selected(
    client_request, service_one
):
    page = client_request.post(
        "main.send_files_by_email_contact_details",
        service_id=SERVICE_ONE_ID,
        _data={
            "contact_details_type": None,
            "url": "",
            "email_address": "",
            "phone_number": "",
        },
        _follow_redirects=True,
    )
    assert (
        normalize_spaces(page.find("span", class_="error-message").text)
        == "Select an option"
    )
    assert normalize_spaces(page.h1.text) == "Send files by email"


@pytest.mark.parametrize(
    ("contact_details_type", "invalid_value", "error"),
    [
        ("url", "invalid.com/", "Must be a valid URL"),
        ("email_address", "me@co", "Enter a valid email address"),
        ("phone_number", "abcde", "Must be a valid phone number"),
    ],
)
def test_send_files_by_email_contact_details_does_not_update_invalid_contact_details(
    mocker,
    client_request,
    service_one,
    contact_details_type,
    invalid_value,
    error,
):
    service_one["contact_link"] = "http://example.com/"
    service_one["permissions"].append(ServicePermission.UPLOAD_DOCUMENT)

    page = client_request.post(
        "main.send_files_by_email_contact_details",
        service_id=SERVICE_ONE_ID,
        _data={
            "contact_details_type": contact_details_type,
            contact_details_type: invalid_value,
        },
        _follow_redirects=True,
    )

    assert error in page.find("span", class_="usa-error-message").text
    assert normalize_spaces(page.h1.text) == "Send files by email"


@pytest.mark.parametrize(
    ("endpoint", "permissions", "expected_p"),
    [
        (
            "main.service_set_auth_type",
            [],
            (
                "Your username, password, and multi-factor authentication options are handled by Login.gov."
            ),
        ),
        (
            "main.service_set_auth_type",
            [ServicePermission.EMAIL_AUTH],
            (
                "Your username, password, and multi-factor authentication options are handled by Login.gov."
            ),
        ),
    ],
)
def test_invitation_pages(
    client_request,
    service_one,
    mock_get_inbound_number_for_service,
    single_sms_sender,
    endpoint,
    permissions,
    expected_p,
):
    service_one["permissions"] = permissions
    page = client_request.get(
        endpoint,
        service_id=SERVICE_ONE_ID,
    )

    assert normalize_spaces(page.select("main p")[0].text) == expected_p


def test_service_settings_when_inbound_number_is_not_set(
    client_request,
    service_one,
    single_reply_to_email_address,
    mock_get_organization,
    single_sms_sender,
    mocker,
    mock_get_free_sms_fragment_limit,
    mock_get_service_data_retention,
):
    mocker.patch(
        "app.inbound_number_client.get_inbound_sms_number_for_service",
        return_value={"data": {}},
    )
    client_request.get(
        "main.service_settings",
        service_id=SERVICE_ONE_ID,
    )


def test_set_inbound_sms_when_inbound_number_is_not_set(
    client_request,
    service_one,
    single_reply_to_email_address,
    single_sms_sender,
    mocker,
):
    mocker.patch(
        "app.inbound_number_client.get_inbound_sms_number_for_service",
        return_value={"data": {}},
    )
    client_request.get(
        "main.service_set_inbound_sms",
        service_id=SERVICE_ONE_ID,
    )


@pytest.mark.parametrize(
    ("user", "expected_paragraphs"),
    [
        (
            create_active_user_with_permissions(),
            [
                "Your service can receive text messages sent to 2028675309.",
                "You can still send text messages from a sender name if you "
                "need to, but users will not be able to reply to those messages.",
                "Contact us if you want to switch this feature off.",
                "You can set up callbacks for received text messages on the API integration page.",
            ],
        ),
        (
            create_active_user_no_api_key_permission(),
            [
                "Your service can receive text messages sent to 2028675309.",
                "You can still send text messages from a sender name if you "
                "need to, but users will not be able to reply to those messages.",
                "Contact us if you want to switch this feature off.",
            ],
        ),
    ],
)
def test_set_inbound_sms_when_inbound_number_is_set(
    client_request,
    service_one,
    mocker,
    user,
    expected_paragraphs,
):
    service_one["permissions"] = [ServicePermission.INBOUND_SMS]
    mocker.patch(
        "app.inbound_number_client.get_inbound_sms_number_for_service",
        return_value={"data": {"number": "2028675309"}},
    )
    client_request.login(user)
    page = client_request.get(
        "main.service_set_inbound_sms",
        service_id=SERVICE_ONE_ID,
    )
    paragraphs = page.select("main p")

    assert len(paragraphs) == len(expected_paragraphs)

    for index, p in enumerate(expected_paragraphs):
        assert normalize_spaces(paragraphs[index].text) == p


def test_show_sms_prefixing_setting_page(
    client_request,
    mock_update_service,
):
    page = client_request.get("main.service_set_sms_prefix", service_id=SERVICE_ONE_ID)
    assert normalize_spaces(page.select_one("legend").text) == (
        "Start all text messages with ‘service one:’"
    )
    radios = page.select("input[type=radio]")
    assert len(radios) == 2
    assert radios[0]["value"] == "True"
    assert radios[0]["checked"] == ""
    assert radios[1]["value"] == "False"
    with pytest.raises(KeyError):
        assert radios[1]["checked"]


@pytest.mark.parametrize(
    "post_value",
    [
        True,
        False,
    ],
)
def test_updates_sms_prefixing(
    client_request,
    mock_update_service,
    post_value,
):
    client_request.post(
        "main.service_set_sms_prefix",
        service_id=SERVICE_ONE_ID,
        _data={"enabled": post_value},
        _expected_redirect=url_for(
            "main.service_settings",
            service_id=SERVICE_ONE_ID,
        ),
    )
    mock_update_service.assert_called_once_with(
        SERVICE_ONE_ID,
        prefix_sms=post_value,
    )


def test_select_organization(
    client_request,
    platform_admin_user,
    service_one,
    mock_get_organization,
    mock_get_organizations,
):
    client_request.login(platform_admin_user)
    page = client_request.get(
        ".link_service_to_organization",
        service_id=service_one["id"],
    )

    assert len(page.select(".usa-radio")) == 3
    for i in range(0, 3):
        assert normalize_spaces(
            page.select(".usa-radio label")[i].text
        ) == "Org {}".format(i + 1)


def test_select_organization_shows_message_if_no_orgs(
    client_request, platform_admin_user, service_one, mock_get_organization, mocker
):
    mocker.patch("app.organizations_client.get_organizations", return_value=[])

    client_request.login(platform_admin_user)
    page = client_request.get(
        ".link_service_to_organization",
        service_id=service_one["id"],
    )

    assert normalize_spaces(page.select_one("main p").text) == "No organizations"
    assert not page.select_one("main button")


def test_update_service_organization(
    client_request,
    platform_admin_user,
    service_one,
    mock_get_organization,
    mock_get_organizations,
    mock_update_service_organization,
):
    client_request.login(platform_admin_user)
    client_request.post(
        ".link_service_to_organization",
        service_id=service_one["id"],
        _data={"organizations": "7aa5d4e9-4385-4488-a489-07812ba13384"},
    )
    mock_update_service_organization.assert_called_once_with(
        service_one["id"], "7aa5d4e9-4385-4488-a489-07812ba13384"
    )


def test_update_service_organization_does_not_update_if_same_value(
    client_request,
    platform_admin_user,
    service_one,
    mock_get_organization,
    mock_get_organizations,
    mock_update_service_organization,
):
    org_id = "7aa5d4e9-4385-4488-a489-07812ba13383"
    service_one["organization"] = org_id
    client_request.login(platform_admin_user)
    client_request.post(
        ".link_service_to_organization",
        service_id=service_one["id"],
        _data={"organizations": org_id},
    )
    assert mock_update_service_organization.called is False


def test_show_service_data_retention(
    client_request,
    platform_admin_user,
    service_one,
    mock_get_service_data_retention,
):
    mock_get_service_data_retention.return_value[0]["days_of_retention"] = 5

    client_request.login(platform_admin_user)
    page = client_request.get(
        "main.data_retention",
        service_id=service_one["id"],
    )

    rows = page.select("tbody tr")
    assert len(rows) == 1
    assert normalize_spaces(rows[0].text) == "Email 5 days Change"


def test_view_add_service_data_retention(
    client_request,
    platform_admin_user,
    service_one,
):
    client_request.login(platform_admin_user)
    page = client_request.get(
        "main.add_data_retention",
        service_id=service_one["id"],
    )
    assert normalize_spaces(page.select_one("input")["value"]) == "email"
    assert page.find("input", attrs={"name": "days_of_retention"})


def test_add_service_data_retention(
    client_request, platform_admin_user, service_one, mock_create_service_data_retention
):
    client_request.login(platform_admin_user)
    client_request.post(
        "main.add_data_retention",
        service_id=service_one["id"],
        _data={"notification_type": "email", "days_of_retention": 5},
        _expected_redirect=url_for(
            "main.data_retention",
            service_id=service_one["id"],
        ),
    )
    assert mock_create_service_data_retention.called


def test_update_service_data_retention(
    client_request,
    platform_admin_user,
    service_one,
    fake_uuid,
    mock_get_service_data_retention,
    mock_update_service_data_retention,
):
    client_request.login(platform_admin_user)
    client_request.post(
        "main.edit_data_retention",
        service_id=service_one["id"],
        data_retention_id=str(fake_uuid),
        _data={"days_of_retention": 5},
        _expected_redirect=url_for(
            "main.data_retention",
            service_id=service_one["id"],
        ),
    )
    assert mock_update_service_data_retention.called


def test_update_service_data_retention_return_validation_error_for_negative_days_of_retention(
    client_request,
    platform_admin_user,
    service_one,
    fake_uuid,
    mock_get_service_data_retention,
    mock_update_service_data_retention,
):
    client_request.login(platform_admin_user)
    page = client_request.post(
        "main.edit_data_retention",
        service_id=service_one["id"],
        data_retention_id=fake_uuid,
        _data={"days_of_retention": -5},
        _expected_status=200,
    )
    assert (
        "Must be between 3 and 90" in page.find("span", class_="usa-error-message").text
    )
    assert mock_get_service_data_retention.called
    assert not mock_update_service_data_retention.called


def test_update_service_data_retention_populates_form(
    client_request,
    platform_admin_user,
    service_one,
    fake_uuid,
    mock_get_service_data_retention,
):
    mock_get_service_data_retention.return_value[0]["days_of_retention"] = 5
    client_request.login(platform_admin_user)
    page = client_request.get(
        "main.edit_data_retention",
        service_id=service_one["id"],
        data_retention_id=fake_uuid,
    )
    assert page.find("input", attrs={"name": "days_of_retention"})["value"] == "5"


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
def test_service_settings_links_to_edit_service_notes_page_for_platform_admins(
    mocker,
    service_one,
    client_request,
    platform_admin_user,
    no_reply_to_email_addresses,
    single_sms_sender,
):
    client_request.login(platform_admin_user)
    page = client_request.get(
        ".service_settings",
        service_id=SERVICE_ONE_ID,
    )
    assert (
        len(
            page.find_all(
                "a", attrs={"href": "/services/{}/notes".format(SERVICE_ONE_ID)}
            )
        )
        == 1
    )


def test_view_edit_service_notes(
    client_request,
    platform_admin_user,
    service_one,
):
    client_request.login(platform_admin_user)
    page = client_request.get(
        "main.edit_service_notes",
        service_id=SERVICE_ONE_ID,
    )
    assert page.select_one("h1").text == "Edit service notes"
    assert page.find("label", class_="usa-label").text.strip() == "Notes"
    assert page.find("textarea").attrs["name"] == "notes"


def test_update_service_notes(
    client_request, platform_admin_user, service_one, mock_update_service
):
    client_request.login(platform_admin_user)
    client_request.post(
        "main.edit_service_notes",
        service_id=SERVICE_ONE_ID,
        _data={"notes": "Very fluffy"},
        _expected_redirect=url_for(
            "main.service_settings",
            service_id=SERVICE_ONE_ID,
        ),
    )
    mock_update_service.assert_called_with(SERVICE_ONE_ID, notes="Very fluffy")


@pytest.mark.usefixtures("_mock_get_service_settings_page_common")
def test_service_settings_links_to_edit_service_billing_details_page_for_platform_admins(
    mocker,
    service_one,
    client_request,
    platform_admin_user,
    no_reply_to_email_addresses,
    single_sms_sender,
):
    client_request.login(platform_admin_user)
    page = client_request.get(
        ".service_settings",
        service_id=SERVICE_ONE_ID,
    )
    assert (
        len(
            page.find_all(
                "a",
                attrs={
                    "href": "/services/{}/edit-billing-details".format(SERVICE_ONE_ID)
                },
            )
        )
        == 1
    )


def test_view_edit_service_billing_details(
    client_request,
    platform_admin_user,
    service_one,
):
    client_request.login(platform_admin_user)
    page = client_request.get(
        "main.edit_service_billing_details",
        service_id=SERVICE_ONE_ID,
    )

    assert page.select_one("h1").text == "Change billing details"
    labels = page.find_all("label", class_="form-label")
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


def test_update_service_billing_details(
    client_request, platform_admin_user, service_one, mock_update_service
):
    client_request.login(platform_admin_user)
    client_request.post(
        "main.edit_service_billing_details",
        service_id=SERVICE_ONE_ID,
        _data={
            "billing_contact_email_addresses": "accounts@fluff.gsa.gov",
            "billing_contact_names": "Flannellette von Fluff",
            "billing_reference": "",
            "purchase_order_number": "PO1234",
            "notes": "very fluffy, give extra allowance",
        },
        _expected_redirect=url_for(
            "main.service_settings",
            service_id=SERVICE_ONE_ID,
        ),
    )
    mock_update_service.assert_called_with(
        SERVICE_ONE_ID,
        billing_contact_email_addresses="accounts@fluff.gsa.gov",
        billing_contact_names="Flannellette von Fluff",
        billing_reference="",
        purchase_order_number="PO1234",
        notes="very fluffy, give extra allowance",
    )
