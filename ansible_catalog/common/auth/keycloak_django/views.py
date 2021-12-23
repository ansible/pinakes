from typing import Optional, Dict

from django.db import models
from django.db.models import QuerySet
from rest_framework.generics import GenericAPIView

from ansible_catalog.common.auth.keycloak_django.permissions import (
    KeycloakPermission, KeycloakPolicy, KeycloakPolicyType,
)


class KeycloakPermissionMixin(GenericAPIView):

    keycloak_resource_type: Optional[str] = None

    keycloak_lookup_field: Optional[str] = "pk"

    keycloak_parent_model: Optional[models.Model] = None

    keycloak_access_policies: Dict[str, KeycloakPolicy] = {
        "list": KeycloakPolicy("read", KeycloakPolicyType.WILDCARD),
        "retrieve": KeycloakPolicy("read", KeycloakPolicyType.OBJECT),
        "create": KeycloakPolicy("create", KeycloakPolicyType.WILDCARD),
        "update": KeycloakPolicy("update", KeycloakPolicyType.OBJECT),
        "partial_update": KeycloakPolicy("update", KeycloakPolicyType.OBJECT),
        "destroy": KeycloakPolicy("delete", KeycloakPolicyType.OBJECT)
    }

    def get_keycloak_access_policies(self) -> Dict[str, KeycloakPolicy]:
        return self.keycloak_access_policies

    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset()
        return KeycloakPermission.scope_queryset(self.request, self, qs)
