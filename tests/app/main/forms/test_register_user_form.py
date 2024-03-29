import pytest

from app.main.forms import RegisterUserForm


@pytest.mark.parametrize("password", ["usnotify"])
def test_should_raise_validation_error_for_password(
    client_request,
    mock_get_user_by_email,
    password,
):
    form = RegisterUserForm()
    form.name.data = "test"
    form.email_address.data = "teset@gsa.gov"
    form.mobile_number.data = "2021231231"
    form.password.data = password

    form.validate()
    assert "Choose a password that’s harder to guess" in form.errors["password"]


def test_valid_email_not_in_valid_domains(
    client_request,
    mock_get_organizations,
):
    form = RegisterUserForm(email_address="test@test.com", mobile_number="2021231231")
    assert not form.validate()
    assert "Enter a public sector email address" in form.errors["email_address"][0]


def test_valid_email_in_valid_domains(
    client_request,
):
    form = RegisterUserForm(
        name="test",
        email_address="test@gsa.gov",
        mobile_number="2028675309",
        password="an uncommon password",
    )
    form.validate()
    assert form.errors == {}


def test_invalid_email_address_error_message(
    client_request,
    mock_get_organizations,
):
    form = RegisterUserForm(
        name="test",
        email_address="test.com",
        mobile_number="2028675309",
        password="1234567890",
    )
    assert not form.validate()

    form = RegisterUserForm(
        name="test",
        email_address="test.com",
        mobile_number="+12028675309",
        password="1234567890",
    )
    assert not form.validate()
