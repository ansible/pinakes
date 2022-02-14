"""Tasks to add/remove portfolio permissions"""
import logging
from django.db import transaction

from automation_services_catalog.common.auth import keycloak_django
from automation_services_catalog.main.common.tasks import (
    add_group_permissions,
    remove_group_permissions,
)
from automation_services_catalog.main.catalog.models import Portfolio

logger = logging.getLogger("catalog")


def add_portfolio_permissions(portfolio_id, groups_ids, permissions):
    """Add group permissions for a portfolio and set share counter"""
    portfolio = Portfolio.objects.get(id=portfolio_id)
    add_group_permissions(portfolio, groups_ids, permissions)
    _update_share_counter(portfolio.keycloak_id)


def remove_portfolio_permissions(portfolio_id, groups_ids, permissions):
    """Remove group permissions for a portfolio and set share counter"""
    portfolio = Portfolio.objects.get(id=portfolio_id)
    remove_group_permissions(portfolio, groups_ids, permissions)
    _update_share_counter(portfolio.keycloak_id)


@transaction.atomic
def _update_share_counter(keycloak_id):
    """Set the share count based on the permission sets in keycloak for this resource."""
    client = keycloak_django.get_uma_client()
    count = len(client.find_permissions_by_resource(keycloak_id))
    Portfolio.objects.filter(keycloak_id=keycloak_id).update(share_count=count)
