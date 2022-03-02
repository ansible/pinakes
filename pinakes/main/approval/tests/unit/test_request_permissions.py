"""Test RequestPermission class"""

from unittest import mock

import pytest

from pinakes.common.auth.keycloak_django.permissions import (
    KeycloakPolicy,
    PermittedResourcesResult,
)
from pinakes.main.approval.permissions import (
    RequestPermission,
)
from pinakes.main.approval.tests.factories import (
    RequestFactory,
)
from pinakes.main.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def _mock_autz_client(mocker):
    mocker.patch(
        "pinakes.common.auth.keycloak_django.clients.get_authz_client"
    )


def _test_get_permissions(type_, action, expected):
    view = mock.Mock(action=action)
    permission = RequestPermission().get_required_permission(
        type_, mock.Mock(), view
    )
    assert permission == expected


def test_queryset_permissions():
    """Test get_required_permission method for QUERYSET type"""
    _test_get_permissions(KeycloakPolicy.Type.QUERYSET, "list", "read")


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        ("retrieve", "read"),
        ("content", "read"),
    ],
)
def test_object_permissions(action, expected):
    """Test get_required_permission method for OBJECT type"""
    _test_get_permissions(KeycloakPolicy.Type.OBJECT, action, expected)


def test_has_permission():
    """Test has_permission method"""
    http_request = mock.Mock()
    view = mock.Mock(action="list")

    permission = RequestPermission()
    assert permission.has_permission(http_request, view) is True


@pytest.mark.django_db
def test_has_object_permission_owner():
    """Test has_object_permission method when user is the owner of the request"""
    user = UserFactory()
    http_request = mock.Mock(user=user)
    view = mock.Mock(action="content")
    request = RequestFactory(user=user)

    permission = RequestPermission()
    assert (
        permission.has_object_permission(http_request, view, request) is True
    )


@pytest.mark.django_db
@mock.patch(
    "pinakes.main.approval.permissions.check_resource_permission",
    return_value=True,
)
def test_has_object_permission_other(check_resource_permission):
    """Test has_object_permission method when user is not the owner of the request"""
    http_request = mock.Mock()
    view = mock.Mock(action="content")
    request = RequestFactory()

    permission = RequestPermission()
    assert (
        permission.has_object_permission(http_request, view, request) is True
    )

    check_resource_permission.assert_called_once_with(
        "approval:request",
        f"approval:request:{request.id}",
        "read",
        mock.ANY,
    )


@mock.patch(
    "pinakes.main.approval.permissions.get_permitted_resources",
    return_value=PermittedResourcesResult(items=[], is_wildcard=True),
)
def test_scope_queryset_wildcard_child_admin(get_permitted_resources):
    """Test scope_query method for nested listing requests as an admin"""
    http_request = mock.Mock()
    http_request.GET.get.return_value = "admin"
    view = mock.Mock(action="list", kwargs={"parent_id": 1})
    qs = mock.Mock()

    permission = RequestPermission()

    assert permission.scope_queryset(http_request, view, qs) is qs

    get_permitted_resources.assert_called_once_with(
        "approval:request",
        "read",
        mock.ANY,
    )


@mock.patch(
    "pinakes.main.approval.permissions.get_permitted_resources",
    return_value=PermittedResourcesResult(items=[], is_wildcard=True),
)
def test_scope_queryset_wildcard_parent_admin(get_permitted_resources):
    """Test scope_query method for listing requests as an admin"""
    http_request = mock.Mock()
    http_request.GET.get.return_value = "admin"
    view = mock.Mock(action="list", kwargs={})
    qs = mock.Mock()
    result_qs = mock.Mock()
    qs.filter.return_value = result_qs

    permission = RequestPermission()

    assert permission.scope_queryset(http_request, view, qs) is result_qs

    qs.filter.assert_called_once_with(parent=None)

    get_permitted_resources.assert_called_once_with(
        "approval:request",
        "read",
        mock.ANY,
    )


@mock.patch(
    "pinakes.main.approval.permissions.get_permitted_resources",
    return_value=PermittedResourcesResult(items=["1", "2"], is_wildcard=True),
)
def test_scope_queryset_filter_approver(get_permitted_resources):
    """Test scope_query method for listing requests as an approver"""
    http_request = mock.Mock()
    http_request.GET.get.return_value = "approver"
    view = mock.Mock(action="list")
    qs = mock.Mock()

    permission = RequestPermission()

    permission.scope_queryset(http_request, view, qs)

    qs.filter.assert_called_once_with(pk__in=["1", "2"])

    get_permitted_resources.assert_called_once_with(
        "approval:request",
        "read",
        mock.ANY,
    )


def test_scope_queryset_filter_owner_parent():
    """Test scope_query method for listing requests as an owner"""
    user = mock.Mock()
    http_request = mock.Mock(user=user)
    http_request.GET.get.return_value = None
    view = mock.Mock(action="list", kwargs={})
    qs = mock.Mock()
    qs_1 = mock.Mock()
    qs.filter.return_value = qs_1

    permission = RequestPermission()
    permission.scope_queryset(http_request, view, qs)

    qs.filter.assert_called_once_with(parent=None)
    qs_1.filter.assert_called_once_with(user=user)


def test_scope_queryset_filter_owner_child():
    """Test scope_query method for nested listing requests as an owner"""
    user = mock.Mock()
    http_request = mock.Mock(user=user)
    http_request.GET.get.return_value = None
    view = mock.Mock(action="list", kwargs={"parent_id": 1})
    qs = mock.Mock()

    permission = RequestPermission()
    permission.scope_queryset(http_request, view, qs)

    qs.filter.assert_called_once_with(user=user)
