from unittest.mock import ANY, call

import pytest

from app import organizations_client


@pytest.mark.parametrize(
    (
        "client_method",
        "expected_cache_get_calls",
        "cache_value",
        "expected_api_calls",
        "expected_cache_set_calls",
        "expected_return_value",
    ),
    [
        (
            "get_domains",
            [
                call("domains"),
            ],
            b"""
                [
                    {"name": "org 1", "domains": ["a", "b", "c"]},
                    {"name": "org 2", "domains": ["c", "d", "e"]}
                ]
            """,
            [],
            [],
            ["a", "b", "c", "d", "e"],
        ),
        (
            "get_domains",
            [
                call("domains"),
                call("organizations"),
            ],
            None,
            [call(url="/organizations")],
            [
                call(
                    "organizations",
                    '[{"domains": ["x", "y", "z"]}]',
                    ex=604800,
                ),
                call("domains", '["x", "y", "z"]', ex=604800),
            ],
            "from api",
        ),
        (
            "get_organizations",
            [
                call("organizations"),
            ],
            b"""
                [
                    {"name": "org 1", "domains": ["a", "b", "c"]},
                    {"name": "org 2", "domains": ["c", "d", "e"]}
                ]
            """,
            [],
            [],
            [
                {"name": "org 1", "domains": ["a", "b", "c"]},
                {"name": "org 2", "domains": ["c", "d", "e"]},
            ],
        ),
        (
            "get_organizations",
            [
                call("organizations"),
            ],
            None,
            [call(url="/organizations")],
            [
                call(
                    "organizations",
                    '[{"domains": ["x", "y", "z"]}]',
                    ex=604800,
                ),
            ],
            "from api",
        ),
    ],
)
def test_returns_value_from_cache(
    notify_admin,
    mocker,
    client_method,
    expected_cache_get_calls,
    cache_value,
    expected_return_value,
    expected_api_calls,
    expected_cache_set_calls,
):
    mock_redis_get = mocker.patch(
        "app.extensions.RedisClient.get",
        return_value=cache_value,
    )
    mock_api_get = mocker.patch(
        "app.notify_client.NotifyAdminAPIClient.get",
        return_value=[{"domains": ["x", "y", "z"]}],
    )
    mock_redis_set = mocker.patch(
        "app.extensions.RedisClient.set",
    )

    getattr(organizations_client, client_method)()

    assert mock_redis_get.call_args_list == expected_cache_get_calls
    assert mock_api_get.call_args_list == expected_api_calls
    assert mock_redis_set.call_args_list == expected_cache_set_calls


def test_deletes_domain_cache(
    notify_admin,
    mock_get_user,
    mocker,
    fake_uuid,
):
    mocker.patch("app.notify_client.current_user", id="1")
    mock_redis_delete = mocker.patch("app.extensions.RedisClient.delete")
    mock_request = mocker.patch(
        "notifications_python_client.base.BaseAPIClient.request"
    )

    organizations_client.update_organization(fake_uuid, foo="bar")

    assert call("domains") in mock_redis_delete.call_args_list
    assert len(mock_request.call_args_list) == 1


@pytest.mark.parametrize(
    ("post_data", "expected_cache_delete_calls"),
    [
        (
            {"foo": "bar"},
            [
                call("organizations"),
                call("domains"),
            ],
        ),
        (
            {"name": "new name"},
            [
                call("organization-6ce466d0-fd6a-11e5-82f5-e0accb9d11a6-name"),
                call("organizations"),
                call("domains"),
            ],
        ),
    ],
)
def test_update_organization_when_not_updating_org_type(
    mocker,
    fake_uuid,
    post_data,
    expected_cache_delete_calls,
):
    mock_redis_delete = mocker.patch("app.extensions.RedisClient.delete")
    mock_post = mocker.patch(
        "app.notify_client.organizations_api_client.OrganizationsClient.post"
    )

    organizations_client.update_organization(fake_uuid, **post_data)

    mock_post.assert_called_with(
        url="/organizations/{}".format(fake_uuid), data=post_data
    )
    assert mock_redis_delete.call_args_list == expected_cache_delete_calls


def test_update_organization_when_updating_org_type_and_org_has_services(
    mocker, fake_uuid
):
    mock_redis_delete = mocker.patch("app.extensions.RedisClient.delete")
    mock_post = mocker.patch(
        "app.notify_client.organizations_api_client.OrganizationsClient.post"
    )

    organizations_client.update_organization(
        fake_uuid,
        cached_service_ids=["a", "b", "c"],
        organization_type="central",
    )

    mock_post.assert_called_with(
        url="/organizations/{}".format(fake_uuid), data={"organization_type": "central"}
    )
    assert mock_redis_delete.call_args_list == [
        call("service-a", "service-b", "service-c"),
        call("organizations"),
        call("domains"),
    ]


def test_update_organization_when_updating_org_type_but_org_has_no_services(
    mocker, fake_uuid
):
    mock_redis_delete = mocker.patch("app.extensions.RedisClient.delete")
    mock_post = mocker.patch(
        "app.notify_client.organizations_api_client.OrganizationsClient.post"
    )

    organizations_client.update_organization(
        fake_uuid,
        cached_service_ids=[],
        organization_type="central",
    )

    mock_post.assert_called_with(
        url="/organizations/{}".format(fake_uuid), data={"organization_type": "central"}
    )
    assert mock_redis_delete.call_args_list == [
        call("organizations"),
        call("domains"),
    ]


def test_update_service_organization_deletes_cache(mocker, fake_uuid):
    mock_redis_delete = mocker.patch("app.extensions.RedisClient.delete")
    mock_post = mocker.patch(
        "app.notify_client.organizations_api_client.OrganizationsClient.post"
    )

    organizations_client.update_service_organization(
        service_id=fake_uuid, org_id=fake_uuid
    )

    assert sorted(mock_redis_delete.call_args_list) == [
        call("live-service-and-organization-counts"),
        call("organizations"),
        call("service-{}".format(fake_uuid)),
    ]
    mock_post.assert_called_with(
        url="/organizations/{}/service".format(fake_uuid), data=ANY
    )


def test_remove_user_from_organization_deletes_user_cache(mocker):
    mock_redis_delete = mocker.patch("app.extensions.RedisClient.delete")
    mock_delete = mocker.patch(
        "app.notify_client.organizations_api_client.OrganizationsClient.delete"
    )

    org_id = "abcd-1234"
    user_id = "efgh-5678"

    organizations_client.remove_user_from_organization(
        org_id=org_id,
        user_id=user_id,
    )

    assert mock_redis_delete.call_args_list == [call(f"user-{user_id}")]
    mock_delete.assert_called_with(f"/organizations/{org_id}/users/{user_id}")
