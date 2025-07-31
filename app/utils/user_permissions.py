from itertools import chain

from app.enums import ServicePermission

permission_mappings = {
    # TODO: consider turning off email-sending permissions during SMS pilot
    ServicePermission.SEND_MESSAGES: [
        ServicePermission.SEND_TEXTS,
        ServicePermission.SEND_EMAILS,
    ],
    ServicePermission.MANAGE_TEMPLATES: [ServicePermission.MANAGE_TEMPLATES],
    ServicePermission.MANAGE_SERVICE: [
        ServicePermission.MANAGE_USERS,
        "manage_settings",
    ],
    "manage_api_keys": ["manage_api_keys"],
    ServicePermission.VIEW_ACTIVITY: [ServicePermission.VIEW_ACTIVITY],
}

all_ui_permissions = set(permission_mappings.keys())
all_db_permissions = set(chain(*permission_mappings.values()))

permission_options = (
    (ServicePermission.VIEW_ACTIVITY, "See dashboard"),
    (ServicePermission.SEND_MESSAGES, "Send messages"),
    (ServicePermission.MANAGE_TEMPLATES, "Add and edit templates"),
    (ServicePermission.MANAGE_SERVICE, "Manage settings, team and usage"),
)


def translate_permissions_from_db_to_ui(db_permissions):
    """
    Given a list of database permissions, return a set of UI permissions

    A UI permission is returned if all of its DB permissions are in the permission list that is passed in.
    Any DB permissions in the list that are not known permissions are also returned.
    """
    unknown_database_permissions = set(db_permissions) - all_db_permissions

    return {
        ui_permission
        for ui_permission, db_permissions_for_ui_permission in permission_mappings.items()
        if set(db_permissions_for_ui_permission) <= set(db_permissions)
    } | unknown_database_permissions


def translate_permissions_from_ui_to_db(ui_permissions):
    """
    Given a list of UI permissions (ie: checkboxes on a permissions edit page), return a set of DB permissions

    Looks them up in the mapping, falling back to just passing through if they're not recognised.
    """
    return set(
        chain.from_iterable(
            permission_mappings.get(ui_permission, [ui_permission])
            for ui_permission in ui_permissions
        )
    )
