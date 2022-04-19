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


class UserCapabilitiesPermission(BaseKeycloakPermission):
    access_policies = {
        "list": KeycloakPolicy("read", KeycloakPolicy.Type.WILDCARD),
        "create": KeycloakPolicy("create", KeycloakPolicy.Type.WILDCARD),
        "retrieve": KeycloakPolicy("read", KeycloakPolicy.Type.OBJECT),
        "update": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "partial_update": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "remove": KeycloakPolicy("delete", KeycloakPolicy.Type.OBJECT),
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


@mock.patch.object(
    UserCapabilitiesPermission, "perform_check_object_permission"
)
def test_user_capabilities(perform_check_object_permission):
    perform_check_object_permission.return_value = True
    expected_result = {
        "retrieve": True,
        "update": True,
        "partial_update": True,
        "remove": True,
    }
    _test_user_capabilities(perform_check_object_permission, expected_result)


@mock.patch.object(
    UserCapabilitiesPermission, "perform_check_object_permission"
)
def test_user_capabilities_read_only(perform_check_object_permission):
    def side_effect(permission, *args, **kwargs):
        return permission == "read"

    perform_check_object_permission.side_effect = side_effect
    expected_result = {
        "retrieve": True,
        "update": False,
        "partial_update": False,
        "remove": False,
    }
    _test_user_capabilities(perform_check_object_permission, expected_result)


def _test_user_capabilities(perform_check_object_permission, expected_result):
    request = mock.Mock(name="request")
    request.method = "GET"
    view = mock.Mock(name="view", action="list")
    obj = mock.Mock(name="obj")

    permission = UserCapabilitiesPermission()
    result = permission.get_user_capabilities(request, view, obj)

    assert result == expected_result

    assert perform_check_object_permission.call_count == 3
    perform_check_object_permission.assert_has_calls(
        [
            mock.call("read", request, view, obj),
            mock.call("update", request, view, obj),
            mock.call("delete", request, view, obj),
        ],
        any_order=True,
    )
