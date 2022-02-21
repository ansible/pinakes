"""PortfolioPermission Module"""
import logging
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import DjangoModelPermissions
from pinakes.common.auth.keycloak_django.permissions import (
    check_wildcard_permission,
    get_permitted_resources,
)
from pinakes.common.auth.keycloak_django.clients import get_authz_client

logger = logging.getLogger("catalog")


class PortfolioPermissions(DjangoModelPermissions):
    """
    The request is authenticated using Django's object-level permissions.
    It requires an object-permissions-enabled backend, such as Django Guardian.
    It ensures that the user is authenticated, and has the appropriate
    `add`/`change`/`delete` permissions on the object using .has_perms.
    This permission can only be applied against view classes that
    provide a `.queryset` attribute.
    """

    perms_map = {
        "list": ["read"],
        "retrieve": ["read"],
        "create": ["create"],
        "update": ["update"],
        "partial_update": ["update"],
        "destroy": ["delete"],
        # Custom actions
        # Icons
        "icon": ["update"],
        # Tags
        "tags": ["read"],
        "tag": ["update"],
        "untag": ["update"],
        # Sharing
        "share": ["update"],
        "unshare": ["update"],
        "share_info": ["update"],
        # Copy
        "copy": ["create", "read"],
    }

    def get_required_object_permissions(self, action, _model_cls):
        """Get the required permissions based on the  current action"""
        if action not in self.perms_map:
            raise MethodNotAllowed(action)

        return self.perms_map[action]

    def has_permission(self, request, view):
        # Workaround to ensure DjangoModelPermissions are not applied
        # to the root view when using DefaultRouter.
        if getattr(view, "_ignore_model_permissions", False):
            return True

        if not request.user or (
            not request.user.is_authenticated and self.authenticated_users_only
        ):
            return False

        if view.action == "create":
            social = request.user.social_auth.get(provider="keycloak-oidc")
            client = get_authz_client(social.extra_data["access_token"])
            return check_wildcard_permission(
                "catalog:portfolio", "create", client
            )

        return True

    def has_object_permission(self, request, view, obj):
        """Check a single objects permission"""
        queryset = self._queryset(view)
        model_cls = queryset.model
        user = request.user

        perms = self.get_required_object_permissions(view.action, model_cls)
        result = get_keycloak_result(user, perms[0], model_cls)
        if result.is_wildcard or str(obj.id) in result.items:
            return True

        return False


def get_keycloak_result(user, requested_perm, model_cls):
    """Get the permissions from keycloak"""
    social = user.social_auth.get(provider="keycloak-oidc")
    client = get_authz_client(social.extra_data["access_token"])
    return get_permitted_resources(
        model_cls.KEYCLOAK_TYPE, requested_perm, client
    )
