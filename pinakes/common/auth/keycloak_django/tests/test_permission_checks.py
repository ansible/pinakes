from unittest import mock

from pinakes.common.auth.keycloak.models import (
    AuthzPermission,
    AuthzResource,
)
from pinakes.common.auth.keycloak_django.permissions import (
    check_wildcard_permission,
    check_resource_permission,
    check_object_permission,
    get_permitted_resources,
)


def test_check_wildcard_permission():
    client = mock.Mock()
    client.check_permissions.return_value = True

    result = check_wildcard_permission("myresource", "read", client)

    assert result is True

    client.check_permissions.assert_called_once_with(
        AuthzPermission("myresource:all", "myresource:read")
    )


def test_check_resource_permission():
    client = mock.Mock()
    client.check_permissions.return_value = True

    result = check_resource_permission(
        "myresource", "myresource:1", "read", client
    )

    assert result is True

    client.check_permissions.assert_called_once_with(
        [
            AuthzPermission("myresource:all", "myresource:read"),
            AuthzPermission("myresource:1", "myresource:read"),
        ]
    )


@mock.patch(
    "pinakes.common.auth.keycloak_django."
    "permissions.check_wildcard_permission",
    return_value=False,
)
@mock.patch(
    "pinakes.common.auth.keycloak_django"
    ".permissions.check_resource_permission",
    return_value=True,
)
def test_check_object_permission_exists(
    check_resource_permission, check_wildcard_permission
):
    obj = mock.Mock()
    obj.keycloak_id = "598802c2-6266-40f0-9558-142e2cb0d98e"
    obj.keycloak_type.return_value = "myresource"
    obj.keycloak_name.return_value = "myresource:1"

    client = mock.Mock()

    assert check_object_permission(obj, "read", client) is True

    check_resource_permission.assert_called_once_with(
        "myresource", "myresource:1", "read", client
    )
    check_wildcard_permission.assert_not_called()


@mock.patch(
    "pinakes.common.auth.keycloak_django"
    ".permissions.check_wildcard_permission",
    return_value=True,
)
@mock.patch(
    "pinakes.common.auth.keycloak_django"
    ".permissions.check_resource_permission",
    return_value=False,
)
def test_check_object_permission_not_exists(
    check_resource_permission, check_wildcard_permission
):
    obj = mock.Mock()
    obj.keycloak_id = None
    obj.keycloak_type.return_value = "myresource"

    client = mock.Mock()

    assert check_object_permission(obj, "read", client) is True

    check_wildcard_permission.assert_called_once_with(
        "myresource", "read", client
    )
    check_resource_permission.assert_not_called()


def test_get_permitted_resources_empty():
    client = mock.Mock()
    client.get_permissions.return_value = []

    result = get_permitted_resources("myresource", "read", client)

    assert result.is_wildcard is False
    assert result.items == []

    client.get_permissions.assert_called_once_with(
        AuthzPermission(scope="myresource:read")
    )


def test_get_permitted_resources_wildcard():
    client = mock.Mock()
    client.get_permissions.return_value = [
        AuthzResource(rsid="0", rsname="myresource:all"),
        AuthzResource(rsid="1", rsname="myresource:1"),
    ]

    result = get_permitted_resources("myresource", "read", client)

    assert result.is_wildcard is True
    assert result.items == ["1"]

    client.get_permissions.assert_called_once_with(
        AuthzPermission(scope="myresource:read")
    )


def test_get_permitted_resources():
    client = mock.Mock()
    client.get_permissions.return_value = [
        AuthzResource(rsid="1", rsname="myresource:1"),
        AuthzResource(rsid="2", rsname="myresource:2"),
    ]

    result = get_permitted_resources("myresource", "read", client)

    assert result.is_wildcard is False
    assert result.items == ["1", "2"]

    client.get_permissions.assert_called_once_with(
        AuthzPermission(scope="myresource:read")
    )
