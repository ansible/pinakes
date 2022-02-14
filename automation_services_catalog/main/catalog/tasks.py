import logging
from django.db import transaction
from django.db.models import F

from automation_services_catalog.main.common.tasks import (
    add_group_permissions,
    remove_group_permissions,
)
from automation_services_catalog.main.catalog.models import Portfolio

logger = logging.getLogger("catalog")


def add_portfolio_permissions(portfolio_id, groups_ids, permissions):
    add_group_permissions(
        Portfolio.objects.get(id=portfolio_id), groups_ids, permissions
    )
    _update_share_counter(portfolio_id, len(groups_ids))


def remove_portfolio_permissions(portfolio_id, groups_ids, permissions):
    remove_group_permissions(
        Portfolio.objects.get(id=portfolio_id), groups_ids, permissions
    )
    _update_share_counter(portfolio_id, -len(groups_ids))


@transaction.atomic
def _update_share_counter(portfolio_id, count):
    """Increment or decrement the share count."""
    Portfolio.objects.filter(id=portfolio_id).update(
        share_count=F("share_count") + count
    )
