from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import (
    ClassVar,
    Dict,
    Union,
    Sequence,
    Optional,
    Any,
    List,
    Iterator,
    Tuple,
)

from django.conf import settings
from django.db import models

from rest_framework import exceptions
from rest_framework.request import Request
from rest_framework.permissions import (
    SAFE_METHODS,
    BasePermission as _BasePermission,
)

from pinakes.common.auth.keycloak import models as keycloak_models
from pinakes.common.auth.keycloak_django import AbstractKeycloakResource
from pinakes.common.auth.keycloak_django.clients import get_authz_client
from pinakes.common.auth.keycloak_django.utils import (
    make_scope_name,
    make_resource_name,
    parse_resource_name,
)

WILDCARD_RESOURCE_ID = "all"


class KeycloakPolicy:
    class Type(enum.Enum):
        WILDCARD = "wildcard"
        OBJECT = "resource"
        QUERYSET = "queryset"

    __slots__ = ("permission", "type")

    def __init__(self, permission, type_):
        self.permission = permission
        self.type = type_


KeycloakPoliciesMap = Dict[
    str, Union[KeycloakPolicy, Sequence[KeycloakPolicy]]
]


# Because DRF includes some hacky piece of code for HTML
# form rendering, which leads wrong objects being passed
# to has_object_permission method, additional type checks may be required.
# See https://github.com/encode/django-rest-framework/issues/2089
# for more details.
class BaseKeycloakPermission(_BasePermission):
    """Base class for keycloak based permission classes.

    To implement a permission class for Keycloak you should inherit this
    permission class and define the `access_policies` class attribute.
    Then override one or more of the following methods in order to
    implement permission checks:
      - `perform_check_permission`
      - `perform_check_object_permission`
      - `perform_scope_queryset`

    These methods are called from the `has_permission`,
    `has_object_permission` and `scope_queryset` methods of
    the permission class respectively, that implement common logic for
    access policies handling.

    Normally you should not override `has_permission`, `has_object_permission`,
    and `scope_queryset` methods directly.
    """

    access_policies: ClassVar[KeycloakPoliciesMap] = {}

    def get_access_policies(
        self, request: Request, view: Any
    ) -> KeycloakPoliciesMap:
        """Returns access policies map.

        Returns `access_policies` attribute of a class by default.
        Can be overridden if finer tuning is required.
        """
        return self.access_policies

    def get_required_permission(
        self, type_: KeycloakPolicy.Type, request: Request, view: Any
    ) -> Optional[str]:
        """Returns required permission for request and policy type.

        Given access policies for permission class, this method returns
        the permission for matched policy type and request (view action).
        If no match found returns None.
        """
        policies_map = self.get_access_policies(request, view)
        try:
            policies = policies_map[view.action]
        except KeyError:
            raise exceptions.MethodNotAllowed(request.method)

        if isinstance(policies, KeycloakPolicy):
            policies = [policies]

        for policy in policies:
            if policy.type == type_:
                return policy.permission
        return None

    def get_user_capabilities(
        self, request: Request, view: Any, obj: Any
    ) -> Dict[str, bool]:
        """
        Evaluates object permission checks for all available actions.

        Returns a mapping of actions and respective permission
        evaluation results.
        """
        permissions = {}
        action_permissions = {}

        policies = (
            item
            for item in _iter_access_policies(
                self.get_access_policies(request, view)
            )
            if item[1].type == KeycloakPolicy.Type.OBJECT
        )

        for action, policy in policies:
            permissions[policy.permission] = None
            action_permissions[action] = policy.permission

        for permission in permissions:
            permissions[permission] = self.perform_check_object_permission(
                permission, request, view, obj
            )

        return {
            action: permissions[permission]
            for action, permission in action_permissions.items()
        }

    def has_permission(self, request: Request, view: Any) -> bool:
        if is_drf_renderer_request(request, view):
            return True
        permission = self.get_required_permission(
            KeycloakPolicy.Type.WILDCARD, request, view
        )
        if permission is None:
            return True
        return self.perform_check_permission(permission, request, view)

    def has_object_permission(
        self, request: Request, view: Any, obj: Any
    ) -> bool:
        permission = self.get_required_permission(
            KeycloakPolicy.Type.OBJECT, request, view
        )
        if permission is None:
            return True
        return self.perform_check_object_permission(
            permission, request, view, obj
        )

    def scope_queryset(
        self, request: Request, view: Any, qs: models.QuerySet
    ) -> models.QuerySet:
        permission = self.get_required_permission(
            KeycloakPolicy.Type.QUERYSET, request, view
        )
        if permission is None:
            return qs
        return self.perform_scope_queryset(permission, request, view, qs)

    def perform_check_permission(
        self, permission: str, request: Request, view: Any
    ) -> bool:
        """Checks wildcard permissions.

        Called for requests that match `WILDCARD` policy type."""
        return True

    def perform_check_object_permission(
        self,
        permission: str,
        request: Request,
        view: Any,
        obj: Any,
    ) -> bool:
        """Checks object permissions.

        Called for requests that match `OBJECT` policy type."""
        return True

    def perform_scope_queryset(
        self, permission: str, request: Request, view: Any, qs: models.QuerySet
    ) -> models.QuerySet:
        """Limits queryset to only permitted resources.

        Called for requests that match `QUERYSET` policy type."""
        return qs


def is_drf_renderer_request(request: Request, view: Any):
    """Checks if a request is intended for the DRF Browsable Renderer.

    For security reasons this is limited only to DEBUG mode.
    """
    return (
        view.action is None
        and request.method in SAFE_METHODS
        and settings.DEBUG
    )


def check_wildcard_permission(
    resource_type: str, permission: str, request: Request
) -> bool:
    scope = make_scope_name(resource_type, permission)
    resource = make_resource_name(resource_type, WILDCARD_RESOURCE_ID)
    client = get_authz_client(request.auth)
    return client.check_permissions(
        keycloak_models.AuthzPermission(
            resource=resource,
            scope=scope,
        )
    )


def check_resource_permission(
    resource_type: str,
    resource_name: str,
    permission: str,
    request: Request,
) -> bool:
    scope = make_scope_name(resource_type, permission)
    wildcard_permission = keycloak_models.AuthzPermission(
        resource=make_resource_name(resource_type, WILDCARD_RESOURCE_ID),
        scope=scope,
    )
    object_permission = keycloak_models.AuthzPermission(
        resource=resource_name,
        scope=scope,
    )
    client = get_authz_client(request.auth)
    return client.check_permissions([wildcard_permission, object_permission])


def check_object_permission(
    obj: AbstractKeycloakResource,
    permission: str,
    request: Request,
):
    if obj.keycloak_id:
        return check_resource_permission(
            obj.keycloak_type(), obj.keycloak_name(), permission, request
        )
    else:
        return check_wildcard_permission(
            obj.keycloak_type(), permission, request
        )


@dataclass(frozen=True)
class PermittedResourcesResult:
    items: List[str]
    is_wildcard: bool


def get_permitted_resources(
    resource_type: str, permission: str, request: Request
) -> PermittedResourcesResult:
    client = get_authz_client(request.auth)
    permissions = client.get_permissions(
        keycloak_models.AuthzPermission(
            scope=make_scope_name(resource_type, permission)
        )
    )

    is_wildcard = False
    resource_ids = []
    for item in permissions:
        type_, id_ = parse_resource_name(item.rsname)
        if resource_type != type_:
            continue
        if id_ == WILDCARD_RESOURCE_ID:
            is_wildcard = True
        else:
            resource_ids.append(id_)
    return PermittedResourcesResult(
        items=resource_ids, is_wildcard=is_wildcard
    )


def _iter_access_policies(
    policy_map: KeycloakPoliciesMap,
) -> Iterator[Tuple[str, KeycloakPolicy]]:
    for action, policy in policy_map.items():
        if isinstance(policy, KeycloakPolicy):
            yield action, policy
        else:
            yield from ((action, item) for item in policy)
