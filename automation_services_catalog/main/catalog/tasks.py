import logging
from django.db import transaction

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
    obj = Portfolio.objects.select_for_update().get(id=portfolio_id)
    if obj:
        obj.share_count += count
        obj.save()
    else:
        logger.error(
            "Portfolio {portfolio_id} not found", portfolio_id=portfolio_id
        )
