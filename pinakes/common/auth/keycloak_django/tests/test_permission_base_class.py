from unittest import mock

import pytest
from rest_framework.exceptions import MethodNotAllowed

from ..permissions import BaseKeycloakPermission, KeycloakPolicy


class TestPermission(BaseKeycloakPermission):
    access_policies = {
        "list": KeycloakPolicy("read", KeycloakPolicy.Type.WILDCARD),
        "list_qs": KeycloakPolicy("read", KeycloakPolicy.Type.QUERYSET),
        "create": KeycloakPolicy("create", KeycloakPolicy.Type.OBJECT),
    }


@pytest.mark.parametrize(
    ("action", "tp", "expected"),
    [
        ("list", KeycloakPolicy.Type.WILDCARD, "read"),
        ("list_qs", KeycloakPolicy.Type.QUERYSET, "read"),
        ("create", KeycloakPolicy.Type.OBJECT, "create"),
    ],
)
def test_get_permission(action, tp, expected):
    request = mock.Mock()
    view = mock.Mock(action=action)
    permission = TestPermission()

    result = permission.get_required_permission(tp, request, view)
    assert result == expected


def test_get_permission_unexpected_action():
    request = mock.Mock()
    request.method = "GET"
    view = mock.Mock(action="unexpected")

    permission = TestPermission()
    with pytest.raises(MethodNotAllowed) as exc:
        permission.get_required_permission(
            KeycloakPolicy.Type.OBJECT, request, view
        )

    assert exc.match('Method "GET" not allowed.')


def test_get_permission_unexpected_type():
    request = mock.Mock()
    request.method = "GET"
    view = mock.Mock(action="list")

    permission = TestPermission()
    result = permission.get_required_permission(
        KeycloakPolicy.Type.OBJECT, request, view
    )

    assert result is None
