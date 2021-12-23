from typing import Optional, Sequence

from ansible_catalog.common.auth.keycloak.uma import UmaClient
from ansible_catalog.common.auth.keycloak import exceptions as keycloak_exc
from ansible_catalog.common.auth.keycloak import models as keycloak_models

from .models import AbstractKeycloakResource
from .utils import make_permission_name, make_scope
from .utils import GroupProto


GROUP_PERMISSION_PREFIX = "group_"


def create_resource_if_not_exists(
    obj: AbstractKeycloakResource, client: UmaClient
) -> Optional[keycloak_models.Resource]:
    if obj.keycloak_id:
        return None

    resource = client.create_resource(
        keycloak_models.Resource(
            name=obj.keycloak_name(),
            type=obj.keycloak_type(),
            scopes=obj.keycloak_scopes(),
            owner_managed_access=True,
        )
    )
    obj.keycloak_id = resource.id
    obj.save()

    return resource


def assign_group_permissions(
    obj: AbstractKeycloakResource,
    group: GroupProto,
    actions: Sequence[str],
    client: UmaClient,
):
    name = make_permission_name(obj, group)
    scopes = [make_scope(obj, action) for action in actions]

    try:
        permission = client.get_permission_by_name(name)
    except keycloak_exc.NoResultFound:
        permission = keycloak_models.UmaPermission(
            name=name, groups=[group.path], scopes=[]
        )

    permission.scopes = list(set(permission.scopes).union(scopes))

    if permission.id:
        if permission.scopes:
            client.update_permission(permission)
        else:
            client.delete_permission(permission.id)
    elif permission.scopes:
        client.create_permission(obj.keycloak_id, permission)


def remove_group_permissions(
    obj: AbstractKeycloakResource,
    group: GroupProto,
    actions: Sequence[str],
    client: UmaClient,
):
    name = make_permission_name(obj, group)
    scopes = [make_scope(obj, action) for action in actions]

    try:
        permission = client.get_permission_by_name(name)
    except keycloak_exc.NoResultFound:
        return

    permission.scopes = list(set(permission.scopes).difference(scopes))

    if permission.scopes:
        client.update_permission(permission)
    else:
        client.delete_permission(permission.id)


def is_group_permission(permission: keycloak_models.UmaPermission):
    return permission.name.startswith(GROUP_PERMISSION_PREFIX)
