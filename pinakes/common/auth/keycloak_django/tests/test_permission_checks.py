from unittest import mock

from pinakes.common.auth.keycloak.models import (
    AuthzPermission,
    AuthzResource,
)

from ..permissions import (
    check_wildcard_permission,
    check_resource_permission,
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

    result = check_resource_permission("myresource", "1", "read", client)

    assert result is True

    client.check_permissions.assert_called_once_with(
        [
            AuthzPermission("myresource:all", "myresource:read"),
            AuthzPermission("myresource:1", "myresource:read"),
        ]
    )


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
    assert result.items is None

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
