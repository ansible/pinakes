"""implement BaseKeycloakPermission classes for approval views"""

from typing import Any

from django.db import models
from rest_framework.request import Request as HttpRequest

from pinakes.common.auth.keycloak_django.clients import (
    get_authz_client,
)
from pinakes.common.auth.keycloak_django.permissions import (
    KeycloakPolicy,
    BaseKeycloakPermission,
    check_wildcard_permission,
    check_resource_permission,
    get_permitted_resources,
)
from pinakes.main.approval.models import (
    Request,
)


class RequestPermission(BaseKeycloakPermission):
    """Permission class for Request view"""

    access_policies = {
        "list": KeycloakPolicy("read", KeycloakPolicy.Type.QUERYSET),
        "retrieve": KeycloakPolicy("read", KeycloakPolicy.Type.OBJECT),
        "content": KeycloakPolicy("read", KeycloakPolicy.Type.OBJECT),
    }

    def perform_check_permission(
        self, permission: str, http_request: HttpRequest, _view: Any
    ) -> bool:
        return check_wildcard_permission(
            Request.keycloak_type(),
            permission,
            get_authz_client(http_request.keycloak_user.access_token),
        )

    def perform_check_object_permission(
        self, permission, http_request: HttpRequest, _view: Any, obj: Request
    ) -> bool:
        if obj.user == http_request.user:
            return True
        return check_resource_permission(
            obj.keycloak_type(),
            obj.keycloak_name(),
            permission,
            get_authz_client(http_request.keycloak_user.access_token),
        )

    def perform_scope_queryset(
        self,
        permission: str,
        http_request: HttpRequest,
        view: Any,
        qs: models.QuerySet,
    ) -> models.QuerySet:
        persona = http_request.GET.get("persona") or "requester"
        if persona == "requester":
            if not "parent_id" in view.kwargs:
                qs = qs.filter(parent=None)
            return qs.filter(user=http_request.user)

        resources = get_permitted_resources(
            Request.keycloak_type(),
            permission,
            get_authz_client(http_request.keycloak_user.access_token),
        )
        if persona == "admin" and resources.is_wildcard:
            if not "parent_id" in view.kwargs:
                qs = qs.filter(parent=None)
            return qs
        return qs.filter(pk__in=resources.items)
