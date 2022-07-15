from unittest import mock

import pytest

from pinakes.common.auth.keycloak_django.permissions import KeycloakPolicy
from pinakes.main.catalog.permissions import ServicePlanPermission
from pinakes.main.catalog.tests.factories import (
    PortfolioItemFactory,
    ServicePlanFactory,
)


def test_get_access_policies_root():
    policies = ServicePlanPermission().get_access_policies(
        request=mock.Mock(), view=mock.Mock(kwargs={"pk": 1})
    )
    assert sorted(policies) == ["partial_update", "reset", "retrieve"]


def test_get_access_policies_nested():
    view = mock.Mock(kwargs={"portfolio_item_id": 1})
    policies = ServicePlanPermission().get_access_policies(
        request=mock.Mock(), view=view
    )
    assert list(policies) == ["list"]


@pytest.mark.parametrize(
    ("action", "expected_permission"),
    [
        ("retrieve", "read"),
        ("partial_update", "update"),
        ("reset", "update"),
    ],
)
def test_required_permission_root(action, expected_permission):
    request = mock.Mock()
    view = mock.Mock(action=action, kwargs={"pk": 1})
    permission = ServicePlanPermission().get_required_permission(
        KeycloakPolicy.Type.WILDCARD, request, view
    )
    assert permission == expected_permission


def test_required_permission_nested():
    request = mock.Mock()
    view = mock.Mock(action="list", kwargs={"portfolio_item_id": 1})
    permission = ServicePlanPermission().get_required_permission(
        KeycloakPolicy.Type.WILDCARD, request, view
    )
    assert permission == "read"


@pytest.fixture
def check_object_permission_mock():
    with mock.patch(
        "pinakes.main.catalog.permissions.check_object_permission"
    ) as patch:
        yield patch


@pytest.fixture
def check_wildcard_permission_mock():
    with mock.patch(
        "pinakes.main.catalog.permissions.check_wildcard_permission"
    ) as patch:
        yield patch


@pytest.mark.django_db
def test_has_object_permission_nested(
    check_object_permission_mock, check_wildcard_permission_mock
):
    check_object_permission_mock.return_value = True

    portfolio_item = PortfolioItemFactory()
    request = mock.Mock()
    view = mock.Mock(
        action="list", kwargs={"portfolio_item_id": portfolio_item.id}
    )
    assert ServicePlanPermission().has_permission(request, view) is True

    check_object_permission_mock.assert_called_once_with(
        portfolio_item.portfolio, "read", request
    )
    check_wildcard_permission_mock.assert_not_called()


@pytest.mark.django_db
def test_has_wildcard_permission_nested(
    check_object_permission_mock, check_wildcard_permission_mock
):
    check_object_permission_mock.return_value = False
    check_wildcard_permission_mock.return_value = True

    portfolio_item = PortfolioItemFactory()
    request = mock.Mock()
    view = mock.Mock(
        action="list", kwargs={"portfolio_item_id": portfolio_item.id}
    )
    assert ServicePlanPermission().has_permission(request, view) is True

    check_object_permission_mock.assert_called_once_with(
        portfolio_item.portfolio, "read", request
    )
    check_wildcard_permission_mock.assert_called_once_with(
        "catalog:service_plan", "read", request
    )


@pytest.mark.django_db
def test_has_object_permission_root(
    check_object_permission_mock, check_wildcard_permission_mock
):
    check_object_permission_mock.return_value = True

    service_plan = ServicePlanFactory()
    request = mock.Mock()
    view = mock.Mock(action="retrieve", kwargs={"pk": service_plan.id})
    assert ServicePlanPermission().has_permission(request, view) is True

    check_object_permission_mock.assert_called_once_with(
        service_plan.portfolio_item.portfolio, "read", request
    )
    check_wildcard_permission_mock.assert_not_called()


@pytest.mark.django_db
def test_has_wildcard_permission_root(
    check_object_permission_mock, check_wildcard_permission_mock
):
    check_object_permission_mock.return_value = False
    check_wildcard_permission_mock.return_value = True

    service_plan = ServicePlanFactory()
    request = mock.Mock()
    view = mock.Mock(action="retrieve", kwargs={"pk": service_plan.id})
    assert ServicePlanPermission().has_permission(request, view) is True

    check_object_permission_mock.assert_called_once_with(
        service_plan.portfolio_item.portfolio, "read", request
    )
    check_wildcard_permission_mock.assert_called_once_with(
        "catalog:service_plan", "read", request
    )
