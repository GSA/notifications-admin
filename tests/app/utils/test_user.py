import pytest
from flask import request
from werkzeug.exceptions import Forbidden

from app.enums import ServicePermission
from app.utils.user import user_has_permissions


@pytest.mark.parametrize(
    "permissions",
    [
        [
            # Route has one of the permissions which the user has
            ServicePermission.MANAGE_SERVICE
        ],
        [
            # Route has more than one of the permissions which the user has
            ServicePermission.MANAGE_TEMPLATES,
            ServicePermission.MANAGE_SERVICE,
        ],
        [
            # Route has one of the permissions which the user has, and one they do not
            ServicePermission.MANAGE_SERVICE,
            ServicePermission.SEND_MESSAGES,
        ],
        [
            # Route has no specific permissions required
        ],
    ],
)
def test_permissions(
    client_request,
    permissions,
    api_user_active,
):
    request.view_args.update({"service_id": "foo"})

    api_user_active["permissions"] = {
        "foo": ["manage_users", "manage_templates", ServicePermission.MANAGE_SETTINGS]
    }
    api_user_active["services"] = ["foo", "bar"]

    client_request.login(api_user_active)

    @user_has_permissions(*permissions)
    def index():
        pass

    index()


@pytest.mark.parametrize(
    "permissions",
    [
        [
            # Route has a permission which the user doesn't have
            ServicePermission.SEND_MESSAGES
        ],
    ],
)
def test_permissions_forbidden(
    client_request,
    permissions,
    api_user_active,
):
    request.view_args.update({"service_id": "foo"})

    api_user_active["permissions"] = {
        "foo": ["manage_users", "manage_templates", ServicePermission.MANAGE_SETTINGS]
    }
    api_user_active["services"] = ["foo", "bar"]

    client_request.login(api_user_active)

    @user_has_permissions(*permissions)
    def index():
        pass

    with pytest.raises(expected_exception=Forbidden):
        index()


def test_restrict_admin_usage(
    client_request,
    platform_admin_user,
):
    request.view_args.update({"service_id": "foo"})
    client_request.login(platform_admin_user)

    @user_has_permissions(restrict_admin_usage=True)
    def index():
        pass

    with pytest.raises(Forbidden):
        index()


def test_no_user_returns_redirect_to_sign_in(client_request, mocker):

    mocker.patch("app.notify_client.user_api_client.UserApiClient.deactivate_user")
    client_request.logout()

    @user_has_permissions()
    def index():
        pass

    response = index()
    assert response.status_code == 302
    assert response.location.startswith("/sign-in?next=")


def test_user_has_permissions_for_organization(
    client_request,
    api_user_active,
):
    api_user_active["organizations"] = ["org_1", "org_2"]
    client_request.login(api_user_active)

    request.view_args = {"org_id": "org_2"}

    @user_has_permissions()
    def index():
        pass

    index()


def test_platform_admin_can_see_orgs_they_dont_have(
    client_request,
    platform_admin_user,
):
    platform_admin_user["organizations"] = []
    client_request.login(platform_admin_user)

    request.view_args = {"org_id": "org_2"}

    @user_has_permissions()
    def index():
        pass

    index()


# def test_cant_use_decorator_without_view_args(
#     client_request,
#     platform_admin_user,
# ):
#     client_request.login(platform_admin_user)

#     request.view_args = {}

#     @user_has_permissions()
#     def index():
#         pass

#     with pytest.raises(NotImplementedError):
#         index()


def test_user_doesnt_have_permissions_for_organization(
    client_request,
    api_user_active,
):
    api_user_active["organizations"] = ["org_1", "org_2"]
    client_request.login(api_user_active)

    request.view_args = {"org_id": "org_3"}

    @user_has_permissions()
    def index():
        pass

    with pytest.raises(Forbidden):
        index()


def test_user_with_no_permissions_to_service_goes_to_templates(
    client_request,
    api_user_active,
):
    api_user_active["permissions"] = {
        "foo": ["manage_users", "manage_templates", ServicePermission.MANAGE_SETTINGS]
    }
    api_user_active["services"] = ["foo", "bar"]
    client_request.login(api_user_active)
    request.view_args = {"service_id": "bar"}

    @user_has_permissions()
    def index():
        pass

    index()
