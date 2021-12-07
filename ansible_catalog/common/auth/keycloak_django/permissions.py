from typing import Any, Tuple, Optional

from django.db.models import QuerySet
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request

from ansible_catalog.common.auth.keycloak import models
from ansible_catalog.common.auth.keycloak_django.clients import (
    get_authz_client,
)

WILDCARD_RESOURCE_ID = "all"


def make_scope_name(resource_type: str, permission: str) -> str:
    return f"{resource_type}:{permission}"


def make_resource_name(resource_type: str, resource_id: str) -> str:
    return f"{resource_type}:{resource_id}"


def parse_resource_name(resource_name: str) -> Tuple[str, str]:
    resource_type, _, resource_id = resource_name.rpartition(":")
    return resource_type, resource_id


class KeycloakPermission(BasePermission):
    def has_permission(self, request: Request, view: Any):
        if view.action is None and request.method in SAFE_METHODS:
            return True

        policy = self._get_policy(view)
        if policy is None:
            return False
        if policy["type"] != "wildcard":
            return True

        client = get_authz_client(request.keycloak_user.access_token)
        resource = make_resource_name(
            view.keycloak_resource_type, WILDCARD_RESOURCE_ID
        )
        scope = make_scope_name(
            view.keycloak_resource_type, policy["permission"]
        )
        return client.check_permissions(
            models.AuthzPermission(
                resource=resource,
                scope=scope,
            )
        )

    def has_object_permission(self, request: Request, view: Any, obj: Any):
        policy = self._get_policy(view)
        if policy is None:
            return False
        if policy["type"] != "object":
            return True

        client = get_authz_client(request.keycloak_user.access_token)
        scope = make_scope_name(
            view.keycloak_resource_type, policy["permission"]
        )
        wildcard_permission = models.AuthzPermission(
            resource=make_resource_name(
                view.keycloak_resource_type, WILDCARD_RESOURCE_ID
            ),
            scope=scope,
        )
        object_permission = models.AuthzPermission(
            resource=make_resource_name(view.keycloak_resource_type, obj.pk),
            scope=scope,
        )
        return client.check_permissions(
            [wildcard_permission, object_permission]
        )

    @classmethod
    def scope_queryset(cls, request: Request, view: Any, qs: QuerySet):
        policy = cls._get_policy(view)
        if policy is None:
            return qs.none()
        if policy["type"] != "queryset":
            return qs

        client = get_authz_client(request.keycloak_user.access_token)
        permissions = client.get_permissions(
            models.AuthzPermission(
                scope=make_scope_name(
                    view.keycloak_resource_type, policy["permission"]
                )
            )
        )

        resource_ids = []
        for permission in permissions:
            resource_type, resource_id = parse_resource_name(permission.rsname)
            if resource_type != view.keycloak_resource_type:
                continue
            if resource_id == WILDCARD_RESOURCE_ID:
                return qs
            # FIXME(cutwater): Support for non integer primary keys needed
            resource_ids.append(int(resource_id))

        return qs.filter(pk__in=resource_ids)

    @classmethod
    def _get_policy(cls, view):
        if view.action is None:
            return None
        return view.keycloak_access_policies.get(view.action)
