from typing import Sequence, Type

from ansible_catalog.common.auth import keycloak_django
from ansible_catalog.common.auth.keycloak_django import (
    AbstractKeycloakResource,
)
from ansible_catalog.main.auth.models import Group


def add_group_permissions(
    obj: AbstractKeycloakResource,
    group_ids: Sequence[str],
    permissions: Sequence[str],
):
    client = keycloak_django.get_uma_client()
    keycloak_django.create_resource_if_not_exists(obj, client)

    groups = Group.objects.filter(id__in=group_ids)
    for group in groups:
        keycloak_django.assign_group_permissions(
            obj, group, permissions, client
        )


def remove_group_permissions(
    obj: AbstractKeycloakResource,
    group_ids: Sequence[str],
    permissions: Sequence[str],
):
    client = keycloak_django.get_uma_client()
    groups = Group.objects.filter(id__in=group_ids)
    for group in groups:
        keycloak_django.remove_group_permissions(
            obj, group, permissions, client
        )
