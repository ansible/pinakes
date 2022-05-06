from unittest import mock

import pytest

from pinakes.common.auth.keycloak_django.permissions import KeycloakPolicy
from pinakes.main.catalog.models import Order
from pinakes.main.catalog.permissions import ProgressMessagePermission
from pinakes.main.catalog.tests.factories import OrderFactory
from pinakes.main.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def _mock_autz_client(mocker):
    mocker.patch(
        "pinakes.common.auth.keycloak_django.clients.get_authz_client"
    )


def _test_get_permissions(type_, action, expected, view_kwargs=None):
    view = mock.Mock(action=action, kwargs=view_kwargs or {})
    permission = ProgressMessagePermission().get_required_permission(
        type_, mock.Mock(), view
    )
    assert permission == expected


@pytest.mark.parametrize(("action", "expected"), [("list", "read")])
def test_wildcard_permissions(action, expected):
    _test_get_permissions(KeycloakPolicy.Type.WILDCARD, action, expected)


@pytest.mark.django_db
@mock.patch(
    "pinakes.main.catalog.permissions.check_wildcard_permission",
    return_value=False,
)
def test_wildcard_is_owner(check_wildcard_permission):
    order = OrderFactory()

    request = mock.Mock()
    request.user = order.user
    view = mock.Mock(
        action="list",
        messageable_model=Order,
        kwargs={"messageable_id": order.id},
    )

    permission = ProgressMessagePermission()
    assert permission.has_permission(request, view) is True

    check_wildcard_permission.assert_not_called()


@pytest.mark.django_db
@mock.patch(
    "pinakes.main.catalog.permissions.check_wildcard_permission",
    return_value=True,
)
def test_wildcard_has_wildcard(check_wildcard_permission):
    user = UserFactory()
    order = OrderFactory()

    request = mock.Mock()
    request.user = user
    view = mock.Mock(
        action="list",
        messageable_model=Order,
        kwargs={"messageable_id": order.id},
    )

    permission = ProgressMessagePermission()
    assert permission.has_permission(request, view) is True

    check_wildcard_permission.assert_called_once_with(
        "catalog:progress_message", "read", request
    )


@pytest.mark.django_db
@mock.patch(
    "pinakes.main.catalog.permissions.check_wildcard_permission",
    return_value=False,
)
def test_wildcard_no_access(check_wildcard_permission):
    user = UserFactory()
    order = OrderFactory()

    request = mock.Mock()
    request.user = user
    view = mock.Mock(
        action="list",
        messageable_model=Order,
        kwargs={"messageable_id": order.id},
    )

    permission = ProgressMessagePermission()
    assert permission.has_permission(request, view) is False

    check_wildcard_permission.assert_called_once_with(
        "catalog:progress_message", "read", request
    )
