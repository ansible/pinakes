"""Test create a portfolio item service"""
import pytest

from ansible_catalog.main.catalog.exceptions import (
    BadParamsException,
)
from ansible_catalog.main.catalog.services.create_portfolio_item import (
    CreatePortfolioItem,
)
from ansible_catalog.main.catalog.tests.factories import (
    PortfolioFactory,
)
from ansible_catalog.main.inventory.tests.factories import (
    ServiceOfferingFactory,
    InventoryServicePlanFactory,
)


@pytest.mark.django_db
def test_process_with_extra_parameters():
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    inventory_service_plan = InventoryServicePlanFactory(
        service_offering=service_offering
    )
    portfolio = PortfolioFactory()
    options = {
        "name": "my test",
        "description": "my test description",
        "portfolio": portfolio.id,
        "service_offering_ref": str(service_offering.id),
    }

    svc = CreatePortfolioItem(options).process()
    item = svc.item
    plan = svc.service_plan

    assert item.name == "my test"
    assert item.description == "my test description"
    assert item.service_offering_ref == str(service_offering.id)
    assert item.service_offering_source_ref == str(service_offering.source.id)
    assert item.portfolio == portfolio
    assert plan.portfolio_item == item
    assert plan.inventory_service_plan_ref == str(inventory_service_plan.id)
    assert plan.name == inventory_service_plan.name
    assert plan.id > 0


@pytest.mark.django_db
def test_process_only_with_required_parameters():
    service_offering = ServiceOfferingFactory()
    portfolio = PortfolioFactory()
    options = {
        "portfolio": portfolio.id,
        "service_offering_ref": str(service_offering.id),
    }

    svc = CreatePortfolioItem(options)
    item = svc.process().item

    assert item.name == service_offering.name
    assert item.service_offering_ref == str(service_offering.id)
    assert item.service_offering_source_ref == str(service_offering.source.id)
    assert item.portfolio == portfolio


@pytest.mark.django_db
def test_process_without_service_offering():
    portfolio = PortfolioFactory()
    options = {
        "portfolio": portfolio.id,
    }

    with pytest.raises(BadParamsException) as excinfo:
        CreatePortfolioItem(options).process()

    assert "Failed to get service offering" in str(excinfo.value)
