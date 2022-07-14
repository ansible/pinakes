import logging
from collections import deque
from typing import Sequence, Iterable

import rq
from django.db import transaction
from django.conf import settings
from django.utils import timezone as django_tz
from django.contrib.sessions.management.commands import clearsessions

from pinakes.common.auth import keycloak_django
from pinakes.common.auth.keycloak import (
    models as keycloak_models,
)
from pinakes.main.common.models import Role, Group

logger = logging.getLogger("approval")


def add_group_permissions(
    obj: keycloak_django.AbstractKeycloakResource,
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
    obj: keycloak_django.AbstractKeycloakResource,
    group_ids: Sequence[str],
    permissions: Sequence[str],
):
    client = keycloak_django.get_uma_client()
    groups = Group.objects.filter(id__in=group_ids)
    for group in groups:
        keycloak_django.remove_group_permissions(
            obj, group, permissions, client
        )


def iter_groups(groups: Iterable[keycloak_models.Group]):
    queue = deque()
    queue.append((None, groups))
    while queue:
        parent, items = queue.popleft()
        for item in items:
            yield parent, item
            if item.sub_groups:
                queue.append((item.id, item.sub_groups))


def sync_external_groups():
    job = rq.get_current_job()
    sync_time = django_tz.now()

    client = keycloak_django.get_admin_client()
    all_groups = client.list_groups(brief_representation=False)

    added_count = 0
    updated_count = 0

    with transaction.atomic():
        for parent_id, group in iter_groups(all_groups):
            obj, created = Group.objects.update_or_create(
                id=group.id,
                defaults={
                    "name": group.name,
                    "path": group.path,
                    "last_sync_time": sync_time,
                    "parent_id": parent_id,
                },
            )

            if created:
                added_count += 1
            else:
                updated_count += 1

            roles = []
            if group.client_roles:
                roles = group.client_roles.get(settings.KEYCLOAK_CLIENT_ID, [])

            _manage_roles(obj, set(roles))
        deleted_count, _ = Group.objects.exclude(
            last_sync_time=sync_time
        ).delete()

    logger.info(
        "Job %s: Group synchronization finished "
        "(added: %d, updated: %d, deleted: %d",
        job.id,
        added_count,
        updated_count,
        deleted_count,
    )


def clear_sessions():
    clearsessions.Command().handle()


def _manage_roles(obj, group_roles):
    existing_role_names = {role.name for role in obj.roles.all()}
    new_role_names = group_roles - existing_role_names

    roles = []
    for role in new_role_names:
        r, _ = Role.objects.get_or_create(name=role)
        roles.append(r)
    obj.roles.add(*roles)

    stale_role_names = existing_role_names - group_roles
    stale_roles = Role.objects.filter(name__in=stale_role_names)
    obj.roles.remove(*stale_roles)
