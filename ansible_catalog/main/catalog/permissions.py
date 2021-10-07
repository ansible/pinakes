from django.conf import settings
from rest_framework.request import Request
from rest_framework.permissions import BasePermission
from ansible_catalog.common.auth.keycloak import KeycloakClient


class PortfolioAccess(BasePermission):

    RESOURCE = "catalog:portfolio"
    ACTION_SCOPE_MAP = {
        "list": "read"
    }

    def has_permission(self, request: Request, view) -> bool:
        if not request.keycloak_user:
            return False
        if view.action == "list":
            return True

        keycloak = KeycloakClient(settings.KEYCLOAK_API_URL)
        access_token = request.keycloak_user.access_token

        return keycloak.check_permissions(
            access_token,
            settings.KEYCLOAK_CLIENT,
            [(self.RESOURCE, f"{self.RESOURCE}:{view.action}")],
        )

    def has_object_permission(self, request: Request, view, obj) -> bool:
        keycloak = KeycloakClient(settings.KEYCLOAK_API_URL)
        access_token = request.keycloak_user.access_token

        return keycloak.check_permissions(
            access_token,
            settings.KEYCLOAK_CLIENT,
            [(f"{self.RESOURCE}:{obj.pk}", f"{self.RESOURCE}:{view.action}")],
        )

    @classmethod
    def scope_queryset(cls, request, action, qs):
        keycloak = KeycloakClient(settings.KEYCLOAK_API_URL)
        access_token = request.keycloak_user.access_token
        action = cls.ACTION_SCOPE_MAP.get(action, action)
        permissions = keycloak.get_permissions(
            access_token,
            settings.KEYCLOAK_CLIENT,
            [("", f"{cls.RESOURCE}:{action}")],
        )
        resource_ids = []
        prefix = f"{cls.RESOURCE}:"
        for permission in permissions:
            rsname = permission["rsname"]
            if rsname == cls.RESOURCE:
                return qs
            if rsname.startswith(prefix):
                id_ = int(rsname[len(prefix):])
                resource_ids.append(id_)
        return qs.filter(pk__in=resource_ids)
