from __future__ import annotations

from typing import Callable, ClassVar, Type, List

from django.db.models import QuerySet
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.permissions import BasePermission

from pinakes.common.auth.keycloak_django.permissions import (
    BaseKeycloakPermission,
)


ScopeQuerysetFn = Callable[[Request, APIView, QuerySet], QuerySet]


class KeycloakPermissionMixin:

    keycloak_permission: ClassVar[Type[BaseKeycloakPermission]]

    def get_keycloak_permission(self) -> BaseKeycloakPermission:
        return self.keycloak_permission()

    def get_permissions(self) -> List[BasePermission]:
        permissions = super().get_permissions()
        keycloak_permission = self.get_keycloak_permission()
        return [*permissions, keycloak_permission]

    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset()
        swagger_view = getattr(self, "swagger_fake_view", False)
        if swagger_view:
            return qs

        permission = self.get_keycloak_permission()
        scope_queryset_fn: ScopeQuerysetFn = getattr(
            permission, "scope_queryset", None
        )
        if scope_queryset_fn:
            qs = scope_queryset_fn(self.request, self, qs)
        return qs
