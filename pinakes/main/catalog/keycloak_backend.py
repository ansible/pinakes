"""Keycloak backend to fetch permissions"""
import logging
from django.contrib.auth.backends import ModelBackend
from pinakes.common.auth.keycloak_django.clients import get_authz_client

logger = logging.getLogger("catalog")


class KeycloakBackend(ModelBackend):
    def get_all_permissions(self, user_obj, obj=None):
        _fetch_keycloak_permissions(user_obj)

        if not user_obj.is_active or user_obj.is_anonymous:
            return set()
        if obj:
            return _get_obj_permissions(
                obj, user_obj._keycloak_authz_resources
            )

        return _get_all_permissions(user_obj._keycloak_authz_resources)


def _fetch_keycloak_permissions(user):
    if not hasattr(user, "_keycloak_authz_resources"):
        logger.info("Fetching permissions from keycloak")
        social = user.social_auth.get(provider="keycloak-oidc")
        client = get_authz_client(social.extra_data["access_token"])
        user._keycloak_authz_resources = client.get_permissions()
        logger.info(user._keycloak_authz_resources)
    else:
        logger.info("Using cached keycloak resources")


def _get_all_permissions(authz_resources):
    permissions = set()
    map_crud = {
        "create": "%(app_label)s.add_%(model_name)s",
        "read": "%(app_label)s.view_%(model_name)s",
        "update": "%(app_label)s.change_%(model_name)s",
        "write": "%(app_label)s.change_%(model_name)s",
        "delete": "%(app_label)s.delete_%(model_name)s",
        "order": "%(app_label)s.order_%(model_name)s",
        "link": "%(app_label)s.change_%(model_name)s",
        "unlink": "%(app_label)s.change_%(model_name)s",
    }
    kwargs = {"app_label": "main"}
    for authz_res in authz_resources:
        if authz_res.rsname.split(":").pop() == "all":
            for scope in authz_res.scopes:
                obj_scope = scope.split(":")
                perm = obj_scope.pop()
                kwargs["model_name"] = obj_scope.pop()
                permissions.add(map_crud[perm] % kwargs)

    return permissions


def _get_obj_permissions(obj, authz_resources):
    matching_names = []
    map_crud = {}
    if obj:
        matching_names = [
            f"{obj.__class__.KEYCLOAK_TYPE}:{obj.id}",
            f"{obj.__class__.KEYCLOAK_TYPE}:all",
        ]
        klass_name = obj.__class__.__name__.lower()
        map_crud = {
            "create": f"main.add_{klass_name}",
            "read": f"main.view_{klass_name}",
            "update": f"main.change_{klass_name}",
            "delete": f"main.delete_{klass_name}",
            "order": f"main.order_{klass_name}",
        }

    permissions = set()
    for authz_res in authz_resources:
        if authz_res.rsname in matching_names:
            for scope in authz_res.scopes:
                permissions.add(map_crud[scope.split(":").pop()])
    return permissions
