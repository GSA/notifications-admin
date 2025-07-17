import pytest

from app.enums import ServicePermission
from app.utils.user_permissions import (
    translate_permissions_from_db_to_ui,
    translate_permissions_from_ui_to_db,
)


@pytest.mark.parametrize(
    ("db_permissions", "expected_ui_permissions"),
    [
        (
            ["manage_templates"],
            {ServicePermission.MANAGE_TEMPLATES},
        ),
        (
            [
                "send_texts",
                "send_emails",
                "manage_templates",
                "some_unknown_permission",
            ],
            {
                ServicePermission.SEND_MESSAGES,
                ServicePermission.MANAGE_TEMPLATES,
                "some_unknown_permission",
            },
        ),
    ],
)
def test_translate_permissions_from_db_to_ui(
    db_permissions,
    expected_ui_permissions,
):
    ui_permissions = translate_permissions_from_db_to_ui(db_permissions)
    assert ui_permissions == expected_ui_permissions


def test_translate_permissions_from_ui_to_db():
    ui_permissions = [
        ServicePermission.SEND_MESSAGES,
        ServicePermission.MANAGE_TEMPLATES,
        "some_unknown_permission",
    ]
    db_permissions = translate_permissions_from_ui_to_db(ui_permissions)

    assert db_permissions == {
        "send_texts",
        "send_emails",
        "manage_templates",
        "some_unknown_permission",
    }
