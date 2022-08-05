from unittest.mock import PropertyMock

import pytest

from app.models.service import Service
from app.utils.branding import (
    NHS_EMAIL_BRANDING_ID,
    get_email_choices,
    get_letter_choices,
)
from tests import organisation_json
from tests.conftest import create_email_branding


@pytest.mark.parametrize('function', [get_email_choices, get_letter_choices])
@pytest.mark.parametrize('org_type, expected_options', [
    ('central', []),
    ('local', []),
    ('nhs_central', [('nhs', 'NHS')]),
])
def test_get_choices_service_not_assigned_to_org(
    service_one,
    function,
    org_type,
    expected_options,
):
    service_one['organisation_type'] = org_type
    service = Service(service_one)

    options = function(service)
    assert list(options) == expected_options


@pytest.mark.parametrize('org_type, branding_id, expected_options', [
    ('central', None, [
        ('govuk_and_org', 'gsa.gov and Test Organisation'),
        ('organisation', 'Test Organisation'),
    ]),
    ('central', 'some-branding-id', [
        ('govuk', 'gsa.gov'),  # central orgs can switch back to gsa.gov
        ('govuk_and_org', 'gsa.gov and Test Organisation'),
        ('organisation', 'Test Organisation'),
    ]),
    ('local', None, [
        ('organisation', 'Test Organisation')
    ]),
    ('local', 'some-branding-id', [
        ('organisation', 'Test Organisation')
    ]),
    ('nhs_central', None, [
        ('nhs', 'NHS')
    ]),
    ('nhs_central', NHS_EMAIL_BRANDING_ID, [
        # don't show NHS if it's the current branding
    ]),
])
def test_get_email_choices_service_assigned_to_org(
    mocker,
    service_one,
    org_type,
    branding_id,
    expected_options,
    mock_get_service_organisation,
    mock_get_email_branding
):
    service = Service(service_one)

    mocker.patch(
        'app.organisations_client.get_organisation',
        return_value=organisation_json(organisation_type=org_type)
    )
    mocker.patch(
        'app.models.service.Service.email_branding_id',
        new_callable=PropertyMock,
        return_value=branding_id
    )

    options = get_email_choices(service)
    assert list(options) == expected_options


@pytest.mark.parametrize('org_type, branding_id, expected_options', [
    ('central', 'some-branding-id', [
        # don't show gsa.gov options as org default supersedes it
        ('organisation', 'Test Organisation'),
    ]),
    ('central', 'org-branding-id', [
        # also don't show org option if it's the current branding
    ]),
    ('local', 'org-branding-id', [
        # don't show org option if it's the current branding
    ]),
])
def test_get_email_choices_org_has_default_branding(
    mocker,
    service_one,
    org_type,
    branding_id,
    expected_options,
    mock_get_service_organisation,
    mock_get_email_branding
):
    service = Service(service_one)

    mocker.patch(
        'app.organisations_client.get_organisation',
        return_value=organisation_json(
            organisation_type=org_type,
            email_branding_id='org-branding-id'
        )
    )
    mocker.patch(
        'app.models.service.Service.email_branding_id',
        new_callable=PropertyMock,
        return_value=branding_id
    )

    options = get_email_choices(service)
    assert list(options) == expected_options


@pytest.mark.parametrize('branding_name, expected_options', [
    ('gsa.gov and something else', [
        ('govuk', 'gsa.gov'),
        ('govuk_and_org', 'gsa.gov and Test Organisation'),
        ('organisation', 'Test Organisation'),
    ]),
    ('gsa.gov and test OrganisatioN', [
        ('govuk', 'gsa.gov'),
        ('organisation', 'Test Organisation'),
    ])
])
def test_get_email_choices_branding_name_in_use(
    mocker,
    service_one,
    branding_name,
    expected_options,
    mock_get_service_organisation,
):
    service = Service(service_one)

    mocker.patch(
        'app.organisations_client.get_organisation',
        return_value=organisation_json(organisation_type='central')
    )
    mocker.patch(
        'app.models.service.Service.email_branding_id',
        new_callable=PropertyMock,
        return_value='some-branding-id',
    )
    mocker.patch(
        'app.email_branding_client.get_email_branding',
        return_value=create_email_branding('_id', {'name': branding_name})
    )

    options = get_email_choices(service)
    # don't show option if its name is similar to current branding
    assert list(options) == expected_options


@pytest.mark.parametrize('org_type, branding_id, expected_options', [
    ('central', None, [
        ('organisation', 'Test Organisation')
    ]),
    ('local', None, [
        ('organisation', 'Test Organisation')
    ]),
    ('local', 'some-random-branding', [
        ('organisation', 'Test Organisation')
    ]),
    ('nhs_central', None, [
        ('nhs', 'NHS')
    ]),
])
def test_get_letter_choices_service_assigned_to_org(
    mocker,
    service_one,
    org_type,
    branding_id,
    expected_options,
    mock_get_service_organisation,
):
    service = Service(service_one)

    mocker.patch(
        'app.organisations_client.get_organisation',
        return_value=organisation_json(organisation_type=org_type)
    )
    mocker.patch(
        'app.models.service.Service.letter_branding_id',
        new_callable=PropertyMock,
        return_value=branding_id,
    )

    options = get_letter_choices(service)
    assert list(options) == expected_options


@pytest.mark.parametrize('branding_id, expected_options', [
    ('some-branding-id', [
        # show org option if it's not the current branding
        ('organisation', 'Test Organisation'),
    ]),
    ('org-branding-id', [
        # don't show org option if it's the current branding
    ]),
])
def test_get_letter_choices_org_has_default_branding(
    mocker,
    service_one,
    branding_id,
    expected_options,
    mock_get_service_organisation,
):
    service = Service(service_one)

    mocker.patch(
        'app.organisations_client.get_organisation',
        return_value=organisation_json(
            organisation_type='central',
            letter_branding_id='org-branding-id'
        )
    )
    mocker.patch(
        'app.models.service.Service.letter_branding_id',
        new_callable=PropertyMock,
        return_value=branding_id
    )

    options = get_letter_choices(service)
    # don't show org option if it's the current branding
    assert list(options) == expected_options


@pytest.mark.parametrize('branding_name, expected_options', [
    ('NHS something else', [
        ('nhs', 'NHS'),
    ]),
    ('NHS', [
        # don't show NHS option if it's the current branding
    ])
])
def test_get_letter_choices_branding_name_in_use(
    mocker,
    service_one,
    branding_name,
    expected_options,
    mock_get_service_organisation,
):
    service = Service(service_one)

    mocker.patch(
        'app.organisations_client.get_organisation',
        return_value=organisation_json(organisation_type='nhs_central')
    )
    mocker.patch(
        'app.models.service.Service.letter_branding_id',
        new_callable=PropertyMock,
        return_value='org-branding-id',
    )
    mocker.patch(
        'app.letter_branding_client.get_letter_branding',
        return_value={'name': branding_name}
    )

    options = get_letter_choices(service)
    assert list(options) == expected_options
