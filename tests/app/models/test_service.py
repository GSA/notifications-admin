import pytest

from app.models.organization import Organization
from app.models.service import Service
from tests import organization_json, service_json
from tests.conftest import ORGANISATION_ID, create_folder, create_template


def test_organization_type_when_services_organization_has_no_org_type(
    mocker, service_one
):
    service = Service(service_one)
    service._dict["organization_id"] = ORGANISATION_ID
    org = organization_json(organization_type=None)
    mocker.patch("app.organizations_client.get_organization", return_value=org)

    assert not org["organization_type"]
    assert service.organization_type == "federal"


def test_organization_type_when_service_and_its_org_both_have_an_org_type(
    mocker, service_one
):
    # service_one has an organization_type of 'central'
    service = Service(service_one)
    service._dict["organization"] = ORGANISATION_ID
    org = organization_json(organization_type="local")
    mocker.patch("app.organizations_client.get_organization", return_value=org)

    assert service.organization_type == "local"


def test_organization_name_comes_from_cache(mocker, service_one):
    mock_redis_get = mocker.patch(
        "app.extensions.RedisClient.get",
        return_value=b'"Borchester Council"',
    )
    mock_get_organization = mocker.patch("app.organizations_client.get_organization")
    service = Service(service_one)
    service._dict["organization"] = ORGANISATION_ID

    assert service.organization_name == "Borchester Council"
    mock_redis_get.assert_called_once_with(f"organization-{ORGANISATION_ID}-name")
    assert mock_get_organization.called is False


def test_organization_name_goes_into_cache(mocker, service_one):
    mocker.patch(
        "app.extensions.RedisClient.get",
        return_value=None,
    )
    mock_redis_set = mocker.patch(
        "app.extensions.RedisClient.set",
    )
    mocker.patch(
        "app.organizations_client.get_organization",
        return_value=organization_json(),
    )
    service = Service(service_one)
    service._dict["organization"] = ORGANISATION_ID

    assert service.organization_name == "Test Organization"
    mock_redis_set.assert_called_once_with(
        f"organization-{ORGANISATION_ID}-name",
        '"Test Organization"',
        ex=604800,
    )


def test_service_without_organization_doesnt_need_org_api(mocker, service_one):
    mock_redis_get = mocker.patch("app.extensions.RedisClient.get")
    mock_get_organization = mocker.patch("app.organizations_client.get_organization")
    service = Service(service_one)
    service._dict["organization"] = None

    assert service.organization_id is None
    assert service.organization_name is None
    assert isinstance(service.organization, Organization)

    assert mock_redis_get.called is False
    assert mock_get_organization.called is False


def test_bad_permission_raises(service_one):
    with pytest.raises(KeyError) as e:
        Service(service_one).has_permission("foo")
    assert str(e.value) == "'foo is not a service permission'"


@pytest.mark.parametrize(
    ("purchase_order_number", "expected_result"),
    [(None, None), ("PO1234", [None, None, None, "PO1234"])],
)
def test_service_billing_details(purchase_order_number, expected_result):
    service = Service(service_json(purchase_order_number=purchase_order_number))
    service._dict["purchase_order_number"] = purchase_order_number
    assert service.billing_details == expected_result


def test_has_templates_of_type_includes_folders(
    mocker,
    service_one,
    mock_get_template_folders,
):
    mocker.patch(
        "app.service_api_client.get_service_templates",
        return_value={
            "data": [create_template(folder="something", template_type="sms")]
        },
    )

    mocker.patch(
        "app.template_folder_api_client.get_template_folders",
        return_value=[create_folder(id="something")],
    )

    assert Service(service_one).has_templates_of_type("sms")
