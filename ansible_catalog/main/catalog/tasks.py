from ansible_catalog.common.tasks import (
    add_group_permissions,
    remove_group_permissions,
)
from ansible_catalog.main.catalog.models import Portfolio


def add_portfolio_permissions(portfolio_id, groups_ids, permissions):
    add_group_permissions(
        Portfolio.objects.get(id=portfolio_id), groups_ids, permissions
    )


def remove_portfolio_permissions(portfolio_id, groups_ids, permissions):
    remove_group_permissions(
        Portfolio.objects.get(id=portfolio_id), groups_ids, permissions
    )
