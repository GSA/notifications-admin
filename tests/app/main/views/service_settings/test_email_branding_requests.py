from unittest.mock import ANY, PropertyMock

import pytest
from flask import url_for
from notifications_utils.clients.zendesk.zendesk_client import (
    NotifySupportTicket,
)

from tests import sample_uuid
from tests.conftest import ORGANISATION_ID, SERVICE_ONE_ID, normalize_spaces


@pytest.mark.parametrize(
    "organization_type, expected_options",
    (
        (
            "other",
            [
                ("something_else", "Something else"),
            ],
        ),
    ),
)
def test_email_branding_request_page_when_no_branding_is_set(
    service_one,
    client_request,
    mocker,
    mock_get_email_branding,
    organization_type,
    expected_options,
):
    service_one["email_branding"] = None
    service_one["organization_type"] = organization_type

    mocker.patch(
        "app.models.service.Service.email_branding_id",
        new_callable=PropertyMock,
        return_value=None,
    )

    page = client_request.get(".email_branding_request", service_id=SERVICE_ONE_ID)

    assert mock_get_email_branding.called is False
    assert page.find_all("iframe")[1]["src"] == url_for(
        "main.email_template", branding_style="__NONE__"
    )

    button_text = normalize_spaces(page.select_one(".page-footer button").text)

    assert [
        (
            radio["value"],
            page.select_one("label[for={}]".format(radio["id"])).text.strip(),
        )
        for radio in page.select("input[type=radio]")
    ] == expected_options

    assert button_text == "Continue"


def test_email_branding_request_page_shows_branding_if_set(
    mocker,
    service_one,
    client_request,
    mock_get_email_branding,
    mock_get_service_organization,
):
    mocker.patch(
        "app.models.service.Service.email_branding_id",
        new_callable=PropertyMock,
        return_value="some-random-branding",
    )

    page = client_request.get(".email_branding_request", service_id=SERVICE_ONE_ID)
    assert page.find_all("iframe")[1]["src"] == url_for(
        "main.email_template", branding_style="some-random-branding"
    )


def test_email_branding_request_page_back_link(
    client_request,
):
    page = client_request.get(".email_branding_request", service_id=SERVICE_ONE_ID)

    back_link = page.select_one("a.usa-back-link")
    assert len(back_link) > 0, "No back link found on the page"
    assert back_link["href"] == url_for(".service_settings", service_id=SERVICE_ONE_ID)


@pytest.mark.parametrize(
    "data, org_type, endpoint",
    (
        (
            {
                "options": "govuk",
            },
            "federal",
            "main.email_branding_govuk",
        ),
        (
            {
                "options": "govuk_and_org",
            },
            "federal",
            "main.email_branding_govuk_and_org",
        ),
        (
            {
                "options": "something_else",
            },
            "federal",
            "main.email_branding_something_else",
        ),
    ),
)
def test_email_branding_request_submit(
    client_request,
    service_one,
    mocker,
    mock_get_email_branding,
    organization_one,
    data,
    org_type,
    endpoint,
):
    organization_one["organization_type"] = org_type
    service_one["email_branding"] = sample_uuid()
    service_one["organization"] = organization_one

    mocker.patch(
        "app.organizations_client.get_organization",
        return_value=organization_one,
    )

    client_request.post(
        ".email_branding_request",
        service_id=SERVICE_ONE_ID,
        _data=data,
        _expected_status=302,
        _expected_redirect=url_for(
            endpoint,
            service_id=SERVICE_ONE_ID,
        ),
    )


def test_email_branding_request_submit_when_no_radio_button_is_selected(
    client_request,
    service_one,
    mock_get_email_branding,
):
    service_one["email_branding"] = sample_uuid()

    page = client_request.post(
        ".email_branding_request",
        service_id=SERVICE_ONE_ID,
        _data={"options": ""},
        _follow_redirects=True,
    )
    assert page.h1.text == "Change email branding"
    assert (
        normalize_spaces(page.select_one(".error-message").text) == "Select an option"
    )


@pytest.mark.parametrize(
    "endpoint, expected_heading",
    [
        ("main.email_branding_govuk_and_org", "Before you request new branding"),
    ],
)
def test_email_branding_description_pages_for_org_branding(
    client_request,
    mocker,
    service_one,
    organization_one,
    mock_get_email_branding,
    endpoint,
    expected_heading,
):
    service_one["email_branding"] = sample_uuid()
    service_one["organization"] = organization_one

    mocker.patch(
        "app.organizations_client.get_organization",
        return_value=organization_one,
    )

    page = client_request.get(
        endpoint,
        service_id=SERVICE_ONE_ID,
    )
    assert page.h1.text == expected_heading
    assert (
        normalize_spaces(page.select_one(".page-footer button").text)
        == "Request new branding"
    )


@pytest.mark.parametrize(
    "endpoint, service_org_type, branding_preview_id",
    [
        ("main.email_branding_govuk", "central", "__NONE__"),
        # ('main.email_branding_nhs', 'nhs_local', NHS_EMAIL_BRANDING_ID),
    ],
)
@pytest.mark.skip(reason="Update for TTS")
def test_email_branding_govuk_and_nhs_pages(
    client_request,
    mocker,
    service_one,
    organization_one,
    mock_get_email_branding,
    endpoint,
    service_org_type,
    branding_preview_id,
):
    organization_one["organization_type"] = service_org_type
    service_one["email_branding"] = sample_uuid()
    service_one["organization"] = organization_one

    mocker.patch(
        "app.organizations_client.get_organization",
        return_value=organization_one,
    )

    page = client_request.get(
        endpoint,
        service_id=SERVICE_ONE_ID,
    )
    assert page.h1.text == "Check your new branding"
    assert "Emails from service one will look like this" in normalize_spaces(page.text)
    assert page.find("iframe")["src"] == url_for(
        "main.email_template", branding_style=branding_preview_id
    )
    assert (
        normalize_spaces(page.select_one(".page-footer button").text)
        == "Use this branding"
    )


@pytest.mark.skip(reason="Update for TTS")
def test_email_branding_something_else_page(client_request, service_one):
    # expect to have a "NHS" option as well as the
    # fallback, so back button goes to choices page
    service_one["organization_type"] = "nhs_central"

    page = client_request.get(
        "main.email_branding_something_else",
        service_id=SERVICE_ONE_ID,
    )
    assert normalize_spaces(page.h1.text) == "Describe the branding you want"
    assert page.select_one("textarea")["name"] == ("something_else")
    assert (
        normalize_spaces(page.select_one(".page-footer button").text)
        == "Request new branding"
    )
    assert page.select_one(".usa-back-link")["href"] == url_for(
        "main.email_branding_request",
        service_id=SERVICE_ONE_ID,
    )


def test_get_email_branding_something_else_page_is_only_option(
    client_request, service_one
):
    # should only have a "something else" option
    # so back button goes back to settings page
    service_one["organization_type"] = "other"

    page = client_request.get(
        "main.email_branding_something_else",
        service_id=SERVICE_ONE_ID,
    )
    assert page.select_one(".usa-back-link")["href"] == url_for(
        "main.service_settings",
        service_id=SERVICE_ONE_ID,
    )


@pytest.mark.parametrize(
    "endpoint",
    [
        ("main.email_branding_govuk"),
        ("main.email_branding_govuk_and_org"),
        ("main.email_branding_organization"),
    ],
)
def test_email_branding_pages_give_404_if_selected_branding_not_allowed(
    client_request,
    endpoint,
):
    # The only email branding allowed is 'something_else', so trying to visit any of the other
    # endpoints gives a 404 status code.
    client_request.get(endpoint, service_id=SERVICE_ONE_ID, _expected_status=404)


def test_email_branding_govuk_submit(
    mocker,
    client_request,
    service_one,
    organization_one,
    no_reply_to_email_addresses,
    mock_get_email_branding,
    single_sms_sender,
    mock_update_service,
):
    mocker.patch(
        "app.organizations_client.get_organization",
        return_value=organization_one,
    )
    mocker.patch(
        "app.models.service.Service.organization_id",
        new_callable=PropertyMock,
        return_value=ORGANISATION_ID,
    )
    service_one["email_branding"] = sample_uuid()

    page = client_request.post(
        ".email_branding_govuk",
        service_id=SERVICE_ONE_ID,
        _follow_redirects=True,
    )

    mock_update_service.assert_called_once_with(
        SERVICE_ONE_ID,
        email_branding=None,
    )
    assert page.h1.text == "Settings"
    assert (
        normalize_spaces(page.select_one(".banner-default").text)
        == "You’ve updated your email branding"
    )


@pytest.mark.skip(reason="Update for TTS")
def test_email_branding_govuk_and_org_submit(
    mocker,
    client_request,
    service_one,
    organization_one,
    no_reply_to_email_addresses,
    mock_get_email_branding,
    single_sms_sender,
):
    mocker.patch(
        "app.organizations_client.get_organization",
        return_value=organization_one,
    )
    mocker.patch(
        "app.models.service.Service.organization_id",
        new_callable=PropertyMock,
        return_value=ORGANISATION_ID,
    )
    service_one["email_branding"] = sample_uuid()

    mock_create_ticket = mocker.spy(NotifySupportTicket, "__init__")
    mock_send_ticket_to_zendesk = mocker.patch(
        "app.main.views.service_settings.zendesk_client.send_ticket_to_zendesk",
        autospec=True,
    )

    page = client_request.post(
        ".email_branding_govuk_and_org",
        service_id=SERVICE_ONE_ID,
        _follow_redirects=True,
    )

    mock_create_ticket.assert_called_once_with(
        ANY,
        message="\n".join(
            [
                "Organization: organization one",
                "Service: service one",
                "http://localhost/services/596364a0-858e-42c8-9062-a8fe822260eb",
                "",
                "---",
                "Current branding: Organization name",
                "Branding requested: GOV.UK and organization one\n",
            ]
        ),
        subject="Email branding request - service one",
        ticket_type="question",
        user_name="Test User",
        user_email="test@user.gsa.gov",
        org_id=ORGANISATION_ID,
        org_type="central",
        service_id=SERVICE_ONE_ID,
    )
    mock_send_ticket_to_zendesk.assert_called_once()
    assert normalize_spaces(page.select_one(".banner-default").text) == (
        "Thanks for your branding request. We’ll get back to you "
        "within one working day."
    )


@pytest.mark.skip(reason="Update for TTS")
def test_email_branding_organization_submit(
    mocker,
    client_request,
    service_one,
    organization_one,
    no_reply_to_email_addresses,
    mock_get_email_branding,
    single_sms_sender,
):
    mocker.patch(
        "app.organizations_client.get_organization",
        return_value=organization_one,
    )
    mocker.patch(
        "app.models.service.Service.organization_id",
        new_callable=PropertyMock,
        return_value=ORGANISATION_ID,
    )
    service_one["email_branding"] = sample_uuid()

    mock_create_ticket = mocker.spy(NotifySupportTicket, "__init__")
    mock_send_ticket_to_zendesk = mocker.patch(
        "app.main.views.service_settings.zendesk_client.send_ticket_to_zendesk",
        autospec=True,
    )

    page = client_request.post(
        ".email_branding_organization",
        service_id=SERVICE_ONE_ID,
        _follow_redirects=True,
    )

    mock_create_ticket.assert_called_once_with(
        ANY,
        message="\n".join(
            [
                "Organization: organization one",
                "Service: service one",
                "http://localhost/services/596364a0-858e-42c8-9062-a8fe822260eb",
                "",
                "---",
                "Current branding: Organization name",
                "Branding requested: organization one\n",
            ]
        ),
        subject="Email branding request - service one",
        ticket_type="question",
        user_name="Test User",
        user_email="test@user.gsa.gov",
        org_id=ORGANISATION_ID,
        org_type="central",
        service_id=SERVICE_ONE_ID,
    )
    mock_send_ticket_to_zendesk.assert_called_once()
    assert normalize_spaces(page.select_one(".banner-default").text) == (
        "Thanks for your branding request. We’ll get back to you "
        "within one working day."
    )


def test_email_branding_something_else_submit(
    client_request,
    mocker,
    service_one,
    no_reply_to_email_addresses,
    mock_get_email_branding,
    single_sms_sender,
):
    service_one["email_branding"] = sample_uuid()
    service_one["organization_type"] = "nhs_local"

    mock_create_ticket = mocker.spy(NotifySupportTicket, "__init__")
    mock_send_ticket_to_zendesk = mocker.patch(
        "app.main.views.service_settings.zendesk_client.send_ticket_to_zendesk",
        autospec=True,
    )

    page = client_request.post(
        ".email_branding_something_else",
        service_id=SERVICE_ONE_ID,
        _data={"something_else": "Homer Simpson"},
        _follow_redirects=True,
    )

    mock_create_ticket.assert_called_once_with(
        ANY,
        message="\n".join(
            [
                "Organization: Can’t tell (domain is user.gsa.gov)",
                "Service: service one",
                "http://localhost/services/596364a0-858e-42c8-9062-a8fe822260eb",
                "",
                "---",
                "Current branding: Organization name",
                "Branding requested: Something else\n",
                "Homer Simpson\n",
            ]
        ),
        subject="Email branding request - service one",
        ticket_type="question",
        user_name="Test User",
        user_email="test@user.gsa.gov",
        org_id=None,
        org_type="nhs_local",
        service_id=SERVICE_ONE_ID,
    )
    mock_send_ticket_to_zendesk.assert_called_once()
    assert normalize_spaces(page.select_one(".banner-default").text) == (
        "Thanks for your branding request. We’ll get back to you "
        "within one working day."
    )


def test_email_branding_something_else_submit_shows_error_if_textbox_is_empty(
    client_request,
):
    page = client_request.post(
        ".email_branding_something_else",
        service_id=SERVICE_ONE_ID,
        _data={"something_else": ""},
        _follow_redirects=True,
    )
    assert normalize_spaces(page.h1.text) == "Describe the branding you want"
    assert (
        normalize_spaces(page.select_one(".usa-error-message").text)
        == "Error: Cannot be empty"
    )
