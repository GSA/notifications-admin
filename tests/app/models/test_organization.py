import pytest

from app.models.organization import Organization
from tests import organization_json


@pytest.mark.parametrize(
    "purchase_order_number,expected_result",
    [[None, None], ["PO1234", [None, None, None, "PO1234"]]],
)
def test_organization_billing_details(purchase_order_number, expected_result):
    organization = Organization(
        organization_json(purchase_order_number=purchase_order_number)
    )
    assert organization.billing_details == expected_result
