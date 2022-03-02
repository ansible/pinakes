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
)

from django.conf import settings
from django.db import models

from rest_framework import exceptions
from rest_framework.request import Request
from rest_framework.permissions import (
    SAFE_METHODS,
    BasePermission as _BasePermission,
)

from pinakes.common.auth.keycloak import (
    models as keycloak_models,
)
from pinakes.common.auth.keycloak.authz import AuthzClient
from pinakes.common.auth.keycloak_django import (
    AbstractKeycloakResource,
)
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
        self, request: Request, view: Any, obj: models.Model
    ) -> bool:
        permission = self.get_required_permission(
            KeycloakPolicy.Type.OBJECT, request, view
        )
        if permission is None:
            return True
        # Because DRF includes some hacky piece of code for HTML
        # form rendering, which leads wrong objects being passed
        # to has_object_permission method, additional checks are required.
        # See https://github.com/encode/django-rest-framework/issues/2089
        # for more details.
        if not isinstance(obj, AbstractKeycloakResource):
            return False
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
        obj: AbstractKeycloakResource,
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
    resource_type: str, permission: str, client: AuthzClient
) -> bool:
    scope = make_scope_name(resource_type, permission)
    resource = make_resource_name(resource_type, WILDCARD_RESOURCE_ID)
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
    client: AuthzClient,
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
    return client.check_permissions([wildcard_permission, object_permission])


@dataclass(frozen=True)
class PermittedResourcesResult:
    items: List[str]
    is_wildcard: bool


def get_permitted_resources(
    resource_type: str, permission: str, client: AuthzClient
) -> PermittedResourcesResult:
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
