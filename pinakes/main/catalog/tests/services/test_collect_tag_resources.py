"""Test on CollectTagResources"""
import pytest

from pinakes.main.catalog.services.collect_tag_resources import (
    CollectTagResources,
)

from pinakes.main.inventory.tests.factories import (
    ServiceInventoryFactory,
    ServiceOfferingFactory,
)
from pinakes.main.catalog.tests.factories import (
    PortfolioFactory,
    PortfolioItemFactory,
    OrderFactory,
    OrderItemFactory,
)


@pytest.mark.django_db
def test_collect_empty_tag_resources():
    """Test on collecting tag resources"""

    service_inventory = ServiceInventoryFactory()
    service_offering = ServiceOfferingFactory(
        service_inventory=service_inventory
    )
    portfolio = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(
        portfolio=portfolio, service_offering_ref=service_offering.id
    )
    order = OrderFactory()
    OrderItemFactory(order=order, portfolio_item=portfolio_item)

    svc = CollectTagResources(order)
    svc.process()

    assert svc.tag_resources == []


@pytest.mark.django_db
def test_collect_remote_tag_resources():
    """Test on collecting tag resources"""

    service_inventory = ServiceInventoryFactory()
    service_inventory.tags.add("/abc")

    service_offering = ServiceOfferingFactory(
        service_inventory=service_inventory
    )
    portfolio = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(
        portfolio=portfolio, service_offering_ref=service_offering.id
    )
    order = OrderFactory()
    OrderItemFactory(order=order, portfolio_item=portfolio_item)

    svc = CollectTagResources(order)
    svc.process()

    assert len(svc.tag_resources) == 1
    assert svc.tag_resources[0]["app_name"] == "inventory"
    assert svc.tag_resources[0]["object_type"] == "ServiceInventory"
    assert svc.tag_resources[0]["tags"][0] == "/abc"


@pytest.mark.django_db
def test_collect_local_tag_resources():
    """Test on collecting tag resources"""

    service_inventory = ServiceInventoryFactory()
    service_offering = ServiceOfferingFactory(
        service_inventory=service_inventory
    )

    portfolio = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(
        portfolio=portfolio, service_offering_ref=service_offering.id
    )
    portfolio.tags.add("/abc")
    portfolio_item.tags.add("/xyz")

    order = OrderFactory()
    OrderItemFactory(order=order, portfolio_item=portfolio_item)

    svc = CollectTagResources(order)
    svc.process()

    assert len(svc.tag_resources) == 2
    assert svc.tag_resources[0]["app_name"] == "catalog"
    assert svc.tag_resources[0]["object_type"] == "Portfolio"
    assert svc.tag_resources[0]["tags"][0] == "/abc"
    assert svc.tag_resources[1]["app_name"] == "catalog"
    assert svc.tag_resources[1]["object_type"] == "PortfolioItem"
    assert svc.tag_resources[1]["tags"][0] == "/xyz"
