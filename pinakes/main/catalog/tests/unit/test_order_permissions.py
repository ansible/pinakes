from unittest import mock

import pytest

from pinakes.common.auth.keycloak_django.permissions import KeycloakPolicy
from pinakes.main.catalog.permissions import OrderPermission
from pinakes.main.catalog.tests.factories import OrderFactory
from pinakes.main.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def _mock_autz_client(mocker):
    mocker.patch(
        "pinakes.common.auth.keycloak_django.clients.get_authz_client"
    )


def _test_get_permissions(type_, action, expected):
    view = mock.Mock(action=action)
    permission = OrderPermission().get_required_permission(
        type_, mock.Mock(), view
    )
    assert permission == expected


@pytest.mark.parametrize(("action", "expected"), [("create", "create")])
def test_wildcard_permissions(action, expected):
    _test_get_permissions(KeycloakPolicy.Type.WILDCARD, action, expected)


@pytest.mark.parametrize(("action", "expected"), [("list", "read")])
def test_queryset_permissions(action, expected):
    _test_get_permissions(KeycloakPolicy.Type.QUERYSET, action, expected)


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        ("retrieve", "read"),
        ("destroy", "delete"),
        ("submit", "update"),
        ("cancel", "update"),
    ],
)
def test_object_permissions(action, expected):
    _test_get_permissions(KeycloakPolicy.Type.OBJECT, action, expected)


@mock.patch(
    "pinakes.main.catalog.permissions.check_wildcard_permission",
    return_value=True,
)
def test_has_permission(check_wildcard_permission):
    request = mock.Mock()
    view = mock.Mock(action="create")

    permission = OrderPermission()
    assert permission.has_permission(request, view) is True


@pytest.mark.django_db
@mock.patch(
    "pinakes.main.catalog.permissions.check_wildcard_permission",
    return_value=True,
)
def test_has_object_permission_wildcard_positive(check_wildcard_permission):
    request = mock.Mock()
    view = mock.Mock(action="retrieve")
    portfolio = OrderFactory()

    permission = OrderPermission()
    assert permission.has_object_permission(request, view, portfolio) is True

    check_wildcard_permission.assert_called_once_with(
        "catalog:order",
        "read",
        mock.ANY,
    )


@pytest.mark.django_db
@mock.patch(
    "pinakes.main.catalog.permissions.check_wildcard_permission",
    return_value=False,
)
def test_has_object_permission_wildcard_negative(check_wildcard_permission):
    user = UserFactory()
    request = mock.Mock(user=user)
    view = mock.Mock(action="retrieve")
    portfolio = OrderFactory(user=user)

    permission = OrderPermission()
    assert permission.has_object_permission(request, view, portfolio) is True

    check_wildcard_permission.assert_called_once_with(
        "catalog:order",
        "read",
        mock.ANY,
    )


@pytest.mark.django_db
@mock.patch(
    "pinakes.main.catalog.permissions.check_wildcard_permission",
    return_value=False,
)
def test_has_object_permission_all_negative(check_wildcard_permission):
    request = mock.Mock(user=UserFactory())
    view = mock.Mock(action="retrieve")
    portfolio = OrderFactory()

    permission = OrderPermission()
    assert permission.has_object_permission(request, view, portfolio) is False

    check_wildcard_permission.assert_called_once_with(
        "catalog:order",
        "read",
        mock.ANY,
    )


@pytest.mark.django_db
@mock.patch(
    "pinakes.main.catalog.permissions.check_wildcard_permission",
    return_value=True,
)
def test_scope_queryset_wildcard_positive(check_wildcard_permission):
    request = mock.Mock()
    view = mock.Mock(action="list")
    qs = mock.Mock()

    permission = OrderPermission()

    assert permission.scope_queryset(request, view, qs) is qs

    check_wildcard_permission.assert_called_once_with(
        "catalog:order",
        "read",
        mock.ANY,
    )


@pytest.mark.django_db
@mock.patch(
    "pinakes.main.catalog.permissions.check_wildcard_permission",
    return_value=False,
)
def test_scope_queryset_filter(get_permitted_resources):
    user = UserFactory()
    request = mock.Mock(user=user)
    view = mock.Mock(action="list")
    qs = mock.Mock()

    permission = OrderPermission()

    permission.scope_queryset(request, view, qs)

    qs.filter.assert_called_with(user=user)

    get_permitted_resources.assert_called_once_with(
        "catalog:order",
        "read",
        mock.ANY,
    )
