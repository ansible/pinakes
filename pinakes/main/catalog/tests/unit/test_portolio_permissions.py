from unittest import mock

import pytest

from pinakes.common.auth.keycloak_django.permissions import (
    KeycloakPolicy,
    PermittedResourcesResult,
)
from pinakes.main.catalog.permissions import (
    PortfolioPermission,
)
from pinakes.main.catalog.tests.factories import (
    PortfolioFactory,
)


@pytest.fixture(autouse=True)
def _mock_autz_client(mocker):
    mocker.patch(
        "pinakes.common.auth.keycloak_django.clients.get_authz_client"
    )


def _test_get_permissions(type_, action, expected):
    view = mock.Mock(action=action)
    permission = PortfolioPermission().get_permission(type_, mock.Mock(), view)
    assert permission == expected


@pytest.mark.parametrize(
    ("action", "expected"), [("create", "create"), ("copy", "create")]
)
def test_wildcard_permissions(action, expected):
    _test_get_permissions(KeycloakPolicy.Type.WILDCARD, action, expected)


@pytest.mark.parametrize(("action", "expected"), [])
def test_queryset_permissions(action, expected):
    _test_get_permissions(KeycloakPolicy.Type.QUERYSET, action, expected)


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        ("retrieve", "read"),
        ("update", "update"),
        ("partial_update", "update"),
        ("icon", "update"),
        ("tags", "read"),
        ("tag", "update"),
        ("untag", "update"),
        ("share", "update"),
        ("unshare", "update"),
        ("share_info", "update"),
        ("copy", "read"),
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
    view = mock.Mock(action="copy")

    permission = PortfolioPermission()
    assert permission.has_permission(request, view) is True

    check_wildcard_permission.assert_called_once_with(
        "catalog:portfolio",
        "create",
        mock.ANY,
    )


@pytest.mark.django_db
@mock.patch(
    "pinakes.main.catalog.permissions.check_resource_permission",
    return_value=True,
)
def test_has_object_permission(check_resource_permission):
    request = mock.Mock()
    view = mock.Mock(action="retrieve")
    portfolio = PortfolioFactory()

    permission = PortfolioPermission()
    assert permission.has_object_permission(request, view, portfolio) is True

    check_resource_permission.assert_called_once_with(
        "catalog:portfolio",
        f"catalog:portfolio:{portfolio.id}",
        "read",
        mock.ANY,
    )


@pytest.mark.django_db
@mock.patch(
    "pinakes.main.catalog.permissions.get_permitted_resources",
    return_value=PermittedResourcesResult(is_wildcard=True),
)
def test_scope_queryset_wildcard(get_permitted_resources):
    request = mock.Mock()
    view = mock.Mock(action="list")
    qs = mock.Mock()

    permission = PortfolioPermission()

    assert permission.scope_queryset(request, view, qs) is qs

    get_permitted_resources.assert_called_once_with(
        "catalog:portfolio",
        "read",
        mock.ANY,
    )


@pytest.mark.django_db
@mock.patch(
    "pinakes.main.catalog.permissions.get_permitted_resources",
    return_value=PermittedResourcesResult(is_wildcard=False, items=["1", "2"]),
)
def test_scope_queryset_filter(get_permitted_resources):
    request = mock.Mock()
    view = mock.Mock(action="list")
    qs = mock.Mock()

    permission = PortfolioPermission()

    permission.scope_queryset(request, view, qs)

    qs.filter.assert_called_with(pk__in=["1", "2"])

    get_permitted_resources.assert_called_once_with(
        "catalog:portfolio",
        "read",
        mock.ANY,
    )
