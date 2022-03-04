"""Test ActionPermission class"""

from unittest import mock

import pytest

from pinakes.main.approval.permissions import (
    ActionPermission,
)
from pinakes.main.approval.tests.factories import RequestFactory, ActionFactory
from pinakes.main.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def _mock_autz_client(mocker):
    mocker.patch(
        "pinakes.common.auth.keycloak_django.clients.get_authz_client"
    )


def test_has_permission_no_request():
    """Test has_permission method without request_id"""
    http_request = mock.Mock()
    view = mock.Mock(kwargs={})
    permission = ActionPermission()
    assert permission.has_permission(http_request, view) is True


@pytest.mark.django_db
@mock.patch(
    "pinakes.main.approval.permissions.check_resource_permission",
    return_value=True,
)
def test_has_permission_with_request(check_resource_permission):
    """Test has_permission method when request_id presents"""
    request = RequestFactory()
    http_request = mock.Mock()
    view = mock.Mock(kwargs={"request_id": request.id})
    permission = ActionPermission()
    assert permission.has_permission(http_request, view) is True

    check_resource_permission.assert_called_once_with(
        "approval:request",
        f"approval:request:{request.id}",
        "read",
        mock.ANY,
    )


@pytest.mark.django_db
def test_has_object_permission_owner():
    """Test has_object_permission method when user is the owner of the request"""
    user = UserFactory()
    http_request = mock.Mock(user=user)
    view = mock.Mock()
    request = RequestFactory(user=user)
    action = ActionFactory(request=request)

    permission = ActionPermission()
    assert permission.has_object_permission(http_request, view, action) is True


@pytest.mark.django_db
@mock.patch(
    "pinakes.main.approval.permissions.check_resource_permission",
    return_value=True,
)
def test_has_object_permission_other(check_resource_permission):
    """Test has_object_permission method when user is not the owner of the request"""
    http_request = mock.Mock()
    view = mock.Mock()
    request = RequestFactory()
    action = ActionFactory(request=request)

    permission = ActionPermission()
    assert permission.has_object_permission(http_request, view, action) is True

    check_resource_permission.assert_called_once_with(
        "approval:request",
        f"approval:request:{request.id}",
        "read",
        mock.ANY,
    )
