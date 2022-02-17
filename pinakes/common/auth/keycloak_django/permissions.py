from __future__ import annotations

import enum
from typing import (
    ClassVar,
    Dict,
    Union,
    Sequence,
    Optional,
    Any,
    NamedTuple,
    List,
)

from django.conf import settings

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

    access_policies: ClassVar[KeycloakPoliciesMap] = {}

    def get_access_policies(self, request: Request, view: Any):
        return self.access_policies

    def get_permission(
        self, type_: KeycloakPolicy.Type, request: Request, view: Any
    ) -> Optional[str]:
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

    def has_permission(self, request, view):
        if is_drf_renderer_request(request, view):
            return True
        permission = self.get_permission(
            KeycloakPolicy.Type.WILDCARD, request, view
        )
        if permission is None:
            return True
        return self.perform_check_permission(permission, request, view)

    def has_object_permission(self, request, view, obj):
        permission = self.get_permission(
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

    def scope_queryset(self, request, view, qs):
        permission = self.get_permission(
            KeycloakPolicy.Type.QUERYSET, request, view
        )
        if permission is None:
            return qs
        return self.perform_scope_queryset(permission, request, view, qs)

    def perform_check_permission(self, permission, request, view):
        return True

    def perform_check_object_permission(self, permission, request, view, obj):
        return True

    def perform_scope_queryset(self, permission, request, view, qs):
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
        resource=make_resource_name(resource_type, resource_name),
        scope=scope,
    )
    return client.check_permissions([wildcard_permission, object_permission])


class PermittedResourcesResult(NamedTuple):
    is_wildcard: bool
    items: Optional[List[str]] = None


def get_permitted_resources(
    resource_type: str, permission: str, client: AuthzClient
) -> PermittedResourcesResult:
    permissions = client.get_permissions(
        keycloak_models.AuthzPermission(
            scope=make_scope_name(resource_type, permission)
        )
    )

    resource_ids = []
    for item in permissions:
        type_, id_ = parse_resource_name(item.rsname)
        if resource_type != type_:
            continue
        if id_ == WILDCARD_RESOURCE_ID:
            return PermittedResourcesResult(is_wildcard=True)
        resource_ids.append(id_)
    return PermittedResourcesResult(is_wildcard=False, items=resource_ids)
