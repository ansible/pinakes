"""Test TemplatePermission class"""

from unittest import mock

import pytest

from pinakes.common.auth.keycloak_django.permissions import KeycloakPolicy
from pinakes.main.approval.permissions import TemplatePermission


@pytest.fixture(autouse=True)
def _mock_autz_client(mocker):
    mocker.patch(
        "pinakes.common.auth.keycloak_django.clients.get_authz_client"
    )


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        ("list", "read"),
        ("retrieve", "read"),
        ("create", "create"),
        ("partial_update", "update"),
        ("destroy", "delete"),
    ],
)
def test_wildcard_permissions(action, expected):
    """Test all wildcard permissions"""
    view = mock.Mock(action=action)
    permission = TemplatePermission().get_required_permission(
        KeycloakPolicy.Type.WILDCARD, mock.Mock(), view
    )
    assert permission == expected


@mock.patch(
    "pinakes.main.approval.permissions.check_wildcard_permission",
    return_value=True,
)
def test_has_permission(check_wildcard_permission):
    """Test has_permission() depends on wildcard permission"""
    request = mock.Mock()
    view = mock.Mock(action="retrieve")

    permission = TemplatePermission()
    assert permission.has_permission(request, view) is True

    check_wildcard_permission.assert_called_once_with(
        "approval:template",
        "read",
        mock.ANY,
    )
