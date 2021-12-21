from dataclasses import dataclass
from enum import Enum
from typing import Any

from django.conf import settings
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request

from ansible_catalog.common.auth.keycloak import models
from ansible_catalog.common.auth.keycloak_django.clients import (
    get_authz_client,
)
from ansible_catalog.common.auth.keycloak_django.utils import make_scope_name, \
    make_resource_name, parse_resource_name

WILDCARD_RESOURCE_ID = "all"


class KeycloakPolicyType(Enum):
    WILDCARD = 1
    OBJECT = 2
    QUERYSET = 3


@dataclass(frozen=True)
class KeycloakPolicy:
    permission: str
    type: KeycloakPolicyType


class KeycloakPermission(BasePermission):
    def has_permission(self, request: Request, view: Any) -> bool:
        if _is_drf_browsable_renderer_request(request, view):
            return True
        policy = _get_view_policy(view)
        if policy is None:
            return False
        if policy.type != KeycloakPolicyType.WILDCARD:
            return True

        parent_model = view.keycloak_parent_model
        lookup_field = view.keycloak_lookup_field
        lookup_value = None

        if parent_model is not None:
            lookup_value = view.kwargs.get(lookup_field)

        if lookup_value is not None:
            obj = get_object_or_404(
                parent_model, **{lookup_field: lookup_value}
            )
            return _check_resource_permission(
                request, view.keycloak_resource_type, policy.permission, obj
            )
        else:
            return _check_wildcard_permission(
                request, view.keycloak_resource_type, policy.permission
            )

    def has_object_permission(
        self, request: Request, view: Any, obj: Any
    ) -> bool:
        policy = _get_view_policy(view)
        if policy is None:
            return False
        if policy.type != KeycloakPolicyType.OBJECT:
            return True

        parent_model = view.keycloak_parent_model
        lookup_field = view.keycloak_lookup_field
        lookup_value = None

        if parent_model is not None:
            lookup_value = getattr(obj, lookup_field)

        if lookup_value is not None:
            obj = get_object_or_404(
                parent_model, **{lookup_field: lookup_value}
            )
            return _check_resource_permission(
                request, view.keycloak_resource_type, policy.permission, obj
            )
        else:
            return _check_resource_permission(
                request, view.keycloak_resource_type, policy.permission, obj
            )

    @classmethod
    def scope_queryset(
        cls,
        request: Request,
        view: Any,
        qs: QuerySet,
    ) -> QuerySet:
        policy = _get_view_policy(view)
        if policy is None:
            return qs.none()
        if policy.type != KeycloakPolicyType.QUERYSET:
            return qs

        lookup_field = view.keycloak_lookup_field

        resource_ids, all_resources = _get_permitted_resources(
            request, view.keycloak_resource_type, policy.permission
        )
        if all_resources:
            return qs
        else:
            return qs.filter(**{f"{lookup_field}__in": resource_ids})


def _is_drf_browsable_renderer_request(request: Request, view: Any) -> bool:
    """Checks if a request is intended for the DRF Browsable Renderer.

    For security reasons this is limited only to DEBUG mode.
    """
    return (
        view.action is None
        and request.method in SAFE_METHODS
        and settings.DEBUG
    )


def _get_view_policy(view):
    if view.action is None:
        return None
    return view.get_keycloak_access_policies().get(view.action)


def _check_resource_permission(request, resource_type, permission, obj):
    client = get_authz_client(request.keycloak_user.access_token)
    scope = make_scope_name(resource_type, permission)
    wildcard_permission = models.AuthzPermission(
        resource=make_resource_name(resource_type, WILDCARD_RESOURCE_ID),
        scope=scope,
    )
    object_permission = models.AuthzPermission(
        resource=make_resource_name(resource_type, obj.pk),
        scope=scope,
    )
    return client.check_permissions([wildcard_permission, object_permission])


def _get_permitted_resources(request, resource_type, permission):
    client = get_authz_client(request.keycloak_user.access_token)
    permissions = client.get_permissions(
        models.AuthzPermission(
            scope=make_scope_name(resource_type, permission)
        )
    )

    resource_ids = []
    for permission in permissions:
        resource_type, resource_id = parse_resource_name(permission.rsname)
        if resource_type != resource_type:
            continue
        if resource_id == WILDCARD_RESOURCE_ID:
            return None, True
        resource_ids.append(resource_id)
    return resource_ids, False


def _check_wildcard_permission(request, resource_type, permission):
    client = get_authz_client(request.keycloak_user.access_token)
    resource = make_resource_name(resource_type, WILDCARD_RESOURCE_ID)
    scope = make_scope_name(resource_type, permission)
    return client.check_permissions(
        models.AuthzPermission(
            resource=resource,
            scope=scope,
        )
    )
