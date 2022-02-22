from unittest import mock

import pytest

from pinakes.common.auth.keycloak_django.permissions import KeycloakPolicy
from pinakes.main.catalog.permissions import OrderItemPermission
from pinakes.main.catalog.tests.factories import (
    OrderItemFactory,
    OrderFactory,
)
from pinakes.main.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def _mock_autz_client(mocker):
    mocker.patch(
        "pinakes.common.auth.keycloak_django.clients.get_authz_client"
    )


def _test_get_permissions(type_, action, expected, view_kwargs=None):
    view = mock.Mock(action=action, kwargs=view_kwargs or {})
    permission = OrderItemPermission().get_required_permission(
        type_, mock.Mock(), view
    )
    assert permission == expected


@pytest.mark.parametrize(("action", "expected"), [("create", "update")])
def test_wildcard_permissions(action, expected):
    _test_get_permissions(KeycloakPolicy.Type.WILDCARD, action, expected)


@pytest.mark.parametrize(("action", "expected"), [("list", "read")])
def test_queryset_permissions(action, expected):
    _test_get_permissions(KeycloakPolicy.Type.QUERYSET, action, expected)


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        ("retrieve", "read"),
        ("destroy", "update"),
    ],
)
def test_object_permissions(action, expected):
    _test_get_permissions(KeycloakPolicy.Type.OBJECT, action, expected)


@pytest.mark.django_db
@mock.patch(
    "pinakes.main.catalog.permissions.check_wildcard_permission",
    return_value=True,
)
def test_has_object_permission_wildcard(check_wildcard_permission):
    item = OrderItemFactory()
    request = mock.Mock()
    view = mock.Mock(action="update", kwargs={})

    permission = OrderItemPermission()
    assert permission.has_object_permission(request, view, item) is True

    check_wildcard_permission.assert_called_once_with(
        "catalog:order",
        "update",
        mock.ANY,
    )


@mock.patch(
    "pinakes.main.catalog.permissions.check_wildcard_permission",
    return_value=False,
)
def _test_has_object_permission_non_wildcard(
    owner, current_user, expected_result, check_wildcard_permission
):
    order = OrderFactory(user=owner)
    item = OrderItemFactory(order=order, user=owner)

    request = mock.Mock(user=current_user)
    view = mock.Mock(action="update", kwargs={})

    permission = OrderItemPermission()
    assert (
        permission.has_object_permission(request, view, item)
        is expected_result
    )

    check_wildcard_permission.assert_called_once_with(
        "catalog:order",
        "update",
        mock.ANY,
    )


@pytest.mark.django_db
def test_has_object_permission_owner():
    user = UserFactory()
    _test_has_object_permission_non_wildcard(user, user, True)


@pytest.mark.django_db
def test_has_object_permission_non_owner():
    owner = UserFactory()
    current_user = UserFactory()
    _test_has_object_permission_non_wildcard(owner, current_user, False)


@mock.patch(
    "pinakes.main.catalog.permissions.check_wildcard_permission",
    return_value=True,
)
def test_scope_queryset_wildcard(check_wildcard_permission):
    request = mock.Mock()
    view = mock.Mock(action="list", kwargs={})
    qs = mock.Mock()

    permission = OrderItemPermission()
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
def test_scope_queryset_non_wildcard(check_wildcard_permission):
    user = UserFactory()
    request = mock.Mock(user=user)
    view = mock.Mock(action="list", kwargs={})
    qs = mock.Mock()

    permission = OrderItemPermission()
    assert permission.scope_queryset(request, view, qs)

    qs.filter.assert_called_with(order__user=user)

    check_wildcard_permission.assert_called_once_with(
        "catalog:order",
        "read",
        mock.ANY,
    )
