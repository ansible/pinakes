"""implement BaseKeycloakPermission classes for approval views"""

from typing import Any

from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework.request import Request as HttpRequest
from rest_framework.permissions import BasePermission

from pinakes.common.auth.keycloak_django.clients import get_authz_client

from pinakes.common.auth.keycloak_django.permissions import (
    KeycloakPolicy,
    BaseKeycloakPermission,
    check_wildcard_permission,
    check_resource_permission,
    get_permitted_resources,
)
from pinakes.main.approval.models import Request, Action


PERSONA_ADMIN = "admin"
PERSONA_USER = "requester"
PERSONA_APPROVER = "approver"


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
        return _request_has_permission(obj, http_request)

    def perform_scope_queryset(
        self,
        permission: str,
        http_request: HttpRequest,
        view: Any,
        qs: models.QuerySet,
    ) -> models.QuerySet:
        persona = http_request.GET.get("persona") or PERSONA_USER
        if persona == PERSONA_USER:
            if not "parent_id" in view.kwargs:
                qs = qs.filter(parent=None)
            return qs.filter(user=http_request.user)

        resources = get_permitted_resources(
            Request.keycloak_type(),
            permission,
            get_authz_client(http_request.keycloak_user.access_token),
        )
        if persona == PERSONA_ADMIN and resources.is_wildcard:
            if not "parent_id" in view.kwargs:
                qs = qs.filter(parent=None)
            return qs
        return qs.filter(pk__in=resources.items)


class ActionPermission(BasePermission):
    """Permission class for Action view"""

    def has_permission(self, http_request: HttpRequest, view: Any) -> bool:
        """override base has_permission()"""

        if not "request_id" in view.kwargs:
            return True

        request = get_object_or_404(Request, pk=view.kwargs["request_id"])
        return _request_has_permission(request, http_request)

    def has_object_permission(
        self, http_request: HttpRequest, view: Any, obj: Action
    ) -> bool:
        """override base has_object_permission()"""

        request = obj.request
        return _request_has_permission(request, http_request)


def _request_has_permission(request, http_request):
    if request.user == http_request.user:
        return True

    return check_resource_permission(
        request.keycloak_type(),
        request.keycloak_name(),
        "read",
        get_authz_client(http_request.keycloak_user.access_token),
    )
