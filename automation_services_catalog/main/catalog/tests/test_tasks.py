"""Test catalog tasks to add/remove permissions"""
import pytest
from django.core.exceptions import ObjectDoesNotExist
from automation_services_catalog.main.catalog.tests.factories import (
    PortfolioFactory,
)
from automation_services_catalog.main.tests.factories import (
    TenantFactory,
    UserFactory,
)
from automation_services_catalog.main.catalog.tasks import (
    add_portfolio_permissions,
    remove_portfolio_permissions,
)


@pytest.mark.django_db
def test_add_portfolio_permissions(mocker):
    """Test adding portfolio permissions"""
    tenant = TenantFactory()
    user = UserFactory(first_name="John", last_name="Doe")
    portfolio = PortfolioFactory(tenant=tenant, user=user)
    group_ids = ["1", "2", "3"]

    mocker.patch(
        "automation_services_catalog.main.catalog.tasks.add_group_permissions"
    )
    add_portfolio_permissions(portfolio.id, group_ids, ["read"])
    portfolio.refresh_from_db()
    assert portfolio.share_count == len(group_ids)


@pytest.mark.django_db
def test_remove_portfolio_permissions(mocker):
    """Test removing portfolio permissions"""
    tenant = TenantFactory()
    user = UserFactory(first_name="John", last_name="Doe")
    group_ids = ["1", "2", "3"]
    portfolio = PortfolioFactory(
        tenant=tenant, user=user, share_count=len(group_ids)
    )

    mocker.patch(
        "automation_services_catalog.main.catalog.tasks.remove_group_permissions"
    )
    remove_portfolio_permissions(portfolio.id, group_ids, ["read"])
    portfolio.refresh_from_db()
    assert portfolio.share_count == 0


@pytest.mark.django_db
def test_remove_missing_portfolio_permissions(mocker):
    """Test removing portfolio permissions from a missing portfolio"""
    group_ids = ["1", "2", "3"]

    mocker.patch(
        "automation_services_catalog.main.catalog.tasks.remove_group_permissions"
    )
    with pytest.raises(ObjectDoesNotExist):
        remove_portfolio_permissions(999999, group_ids, ["read"])
