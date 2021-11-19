import logging
from collections import deque
from typing import Iterable

import rq
from django.db import transaction
from django.utils import timezone as django_tz

from ansible_catalog.common.auth import keycloak_django
from ansible_catalog.common.auth.keycloak import models as keycloak_models
from ansible_catalog.main.auth.models import Group


logger = logging.getLogger("approval")


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
    all_groups = client.list_groups()

    added_count = 0
    updated_count = 0

    with transaction.atomic():
        for parent_id, group in iter_groups(all_groups):
            _, created = Group.objects.update_or_create(
                id=group.id,
                defaults=dict(
                    name=group.name,
                    path=group.path,
                    last_sync_time=sync_time,
                    parent_id=parent_id,
                ),
            )

            if created:
                added_count += 1
            else:
                updated_count += 1

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
