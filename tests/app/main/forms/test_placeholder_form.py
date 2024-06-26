import pytest

from app.main.forms import get_placeholder_form_instance


def test_form_class_not_mutated(notify_admin):
    with notify_admin.test_request_context(
        method="POST", data={"placeholder_value": ""}
    ):
        form1 = get_placeholder_form_instance("name", {}, "sms")
        form2 = get_placeholder_form_instance("city", {}, "sms")

        assert not form1.validate_on_submit()
        assert not form2.validate_on_submit()

        assert (
            str(form1.placeholder_value.label)
            == '<label for="placeholder_value">name</label>'
        )
        assert (
            str(form2.placeholder_value.label)
            == '<label for="placeholder_value">city</label>'
        )


@pytest.mark.parametrize(
    (
        "service_can_send_international_sms",
        "placeholder_name",
        "template_type",
        "value",
        "expected_error",
    ),
    [
        (False, "email address", "email", "", "Cannot be empty"),
        (False, "email address", "email", "12345", "Enter a valid email address"),
        (
            False,
            "email address",
            "email",
            "“bad”@email-address.com",
            "Enter a valid email address",
        ),
        (False, "email address", "email", "test@example.com", None),
        (False, "email address", "email", "test@example.gsa.gov", None),
        (False, "phone number", "sms", "", "Cannot be empty"),
        (False, "phone number", "sms", "+(44) 7700-900 855", "Not a US number"),
        (False, "phone number", "sms", "2028675309", None),
        (False, "phone number", "sms", "+1 (202) 867-5309", None),
        (True, "phone number", "sms", "+123", "Not enough digits"),
        (True, "phone number", "sms", "+1-2345-678890", None),
        (False, "anything else", "sms", "", "Cannot be empty"),
        (False, "anything else", "email", "", "Cannot be empty"),
        (
            True,
            "phone number",
            "sms",
            "invalid",
            "The string supplied did not seem to be a phone number.",
        ),
        (True, "phone number", "email", "invalid", None),
        (True, "email address", "sms", "invalid", None),
    ],
)
def test_validates_recipients(
    notify_admin,
    placeholder_name,
    template_type,
    value,
    service_can_send_international_sms,
    expected_error,
):
    with notify_admin.test_request_context(
        method="POST", data={"placeholder_value": value}
    ):
        form = get_placeholder_form_instance(
            placeholder_name,
            {},
            template_type,
            allow_international_phone_numbers=service_can_send_international_sms,
        )

        if expected_error:
            assert not form.validate_on_submit()
            assert form.placeholder_value.errors[0] == expected_error
        else:
            assert form.validate_on_submit()
