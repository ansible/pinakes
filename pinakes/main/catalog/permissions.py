from typing import Any

from django.db import models
from rest_framework.request import Request

from pinakes.common.auth.keycloak_django import (
    AbstractKeycloakResource,
)
from pinakes.common.auth.keycloak_django.clients import (
    get_authz_client,
)
from pinakes.common.auth.keycloak_django.permissions import (
    is_drf_renderer_request,
    KeycloakPolicy,
    BaseKeycloakPermission,
    check_wildcard_permission,
    check_resource_permission,
    get_permitted_resources,
)
from pinakes.main.catalog.models import (
    Portfolio,
)

# FIXME(cutwater): Permission classes share a lot of common code and must be
#   refactored


class PortfolioPermission(BaseKeycloakPermission):

    access_policies = {
        "list": KeycloakPolicy("read", KeycloakPolicy.Type.QUERYSET),
        "retrieve": KeycloakPolicy("read", KeycloakPolicy.Type.OBJECT),
        "create": KeycloakPolicy("create", KeycloakPolicy.Type.WILDCARD),
        "update": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "partial_update": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "destroy": KeycloakPolicy("delete", KeycloakPolicy.Type.OBJECT),
        # Custom actions
        # Icons
        "icon": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        # Tags
        "tags": KeycloakPolicy("read", KeycloakPolicy.Type.OBJECT),
        "tag": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "untag": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        # Sharing
        "share": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "unshare": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "share_info": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        # Copy
        "copy": [
            KeycloakPolicy("create", KeycloakPolicy.Type.WILDCARD),
            KeycloakPolicy("read", KeycloakPolicy.Type.OBJECT),
        ],
    }

    def perform_check_permission(
        self, permission: str, request: Request, view: Any
    ) -> bool:
        return check_wildcard_permission(
            Portfolio.keycloak_type(),
            permission,
            get_authz_client(request.keycloak_user.access_token),
        )

    def perform_check_object_permission(
        self, permission, request: Request, view: Any, obj: Portfolio
    ) -> bool:
        return check_resource_permission(
            obj.keycloak_type(),
            obj.keycloak_name(),
            permission,
            get_authz_client(request.keycloak_user.access_token),
        )

    def perform_scope_queryset(
        self,
        permission: str,
        request: Request,
        view: Any,
        qs: models.QuerySet,
    ) -> models.QuerySet:
        resources = get_permitted_resources(
            Portfolio.keycloak_type(),
            permission,
            get_authz_client(request.keycloak_user.access_token),
        )
        if resources.is_wildcard:
            return qs
        else:
            return qs.filter(pk__in=resources.items)
