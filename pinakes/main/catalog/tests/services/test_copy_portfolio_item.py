"""Test copy portfolio item service"""
import pytest

from pinakes.main.catalog.models import ServicePlan, PortfolioItem
from pinakes.main.catalog.services.copy_portfolio_item import CopyPortfolioItem
from pinakes.main.catalog.tests.factories import (
    PortfolioFactory,
    PortfolioItemFactory,
    ServicePlanFactory,
)
from pinakes.main.inventory.tests.factories import (
    InventoryServicePlanFactory,
    ServiceOfferingFactory,
)

SCHEMA = {
    "schemaType": "default",
    "schema": {
        "fields": [
            {
                "label": "Number of Job templates",
                "name": "dev_null",
                "initialValue": 8,
                "helperText": "Number of Job templates on this workflow",
                "isRequired": True,
                "component": "text-field",
                "type": "number",
                "dataType": "integer",
                "options": [{"label": "", "value": ""}],
                "validate": [
                    {"type": "required-validator"},
                    {"type": "min-number-value", "value": 0},
                    {"type": "max-number-value", "value": 100},
                ],
            }
        ],
        "title": "",
        "description": "",
    },
}


@pytest.mark.django_db
def test_is_orderable_with_null_service_offering():
    portfolio = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(portfolio=portfolio)

    svc = CopyPortfolioItem(
        portfolio_item, portfolio, portfolio_item_name="my test"
    )
    orderable = svc._is_orderable()

    assert orderable is False


@pytest.mark.django_db
def test_is_orderable_with_empty_service_plans():
    service_offering = ServiceOfferingFactory()
    portfolio = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id),
        portfolio=portfolio,
    )
    svc = CopyPortfolioItem(portfolio_item, portfolio_item_name="my test")
    orderable = svc._is_orderable()

    assert orderable is True


@pytest.mark.django_db
def test_is_orderable_with_service_plans():
    service_offering = ServiceOfferingFactory()
    InventoryServicePlanFactory(
        create_json_schema=SCHEMA, service_offering=service_offering
    )
    portfolio = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id),
        portfolio=portfolio,
    )
    ServicePlanFactory(base_schema={}, portfolio_item=portfolio_item)

    svc = CopyPortfolioItem(portfolio_item, portfolio_item_name="my test")
    orderable = svc._is_orderable()

    assert orderable is True


@pytest.mark.django_db
def test_copy_portfolio_items_to_the_same_portfolio():
    service_offering = ServiceOfferingFactory()
    InventoryServicePlanFactory(
        create_json_schema=SCHEMA, service_offering=service_offering
    )

    portfolio = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id),
        portfolio=portfolio,
    )
    ServicePlanFactory(portfolio_item=portfolio_item)

    assert PortfolioItem.objects.count() == 1
    assert ServicePlan.objects.count() == 1

    svc = CopyPortfolioItem(
        portfolio_item, portfolio_item_name=portfolio_item.name
    )
    svc.process()

    assert PortfolioItem.objects.count() == 2
    assert (
        PortfolioItem.objects.last().name == f"Copy of {portfolio_item.name}"
    )
    assert portfolio_item.portfolio == PortfolioItem.objects.last().portfolio

    assert ServicePlan.objects.count() == 2
    assert ServicePlan.objects.first().name == ServicePlan.objects.last().name


@pytest.mark.django_db
def test_copy_portfolio_items_to_different_portfolios():
    service_offering = ServiceOfferingFactory()
    InventoryServicePlanFactory(
        create_json_schema=SCHEMA, service_offering=service_offering
    )

    portfolio_1 = PortfolioFactory()
    portfolio_2 = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(
        portfolio=portfolio_1,
        service_offering_ref=str(service_offering.id),
    )

    assert PortfolioItem.objects.count() == 1
    assert PortfolioItem.objects.filter(portfolio=portfolio_2).count() == 0

    svc = CopyPortfolioItem(portfolio_item, portfolio_2)
    svc.process()

    assert PortfolioItem.objects.count() == 2
    assert PortfolioItem.objects.filter(portfolio=portfolio_2).count() == 1
    assert (
        PortfolioItem.objects.filter(portfolio=portfolio_2).first().name
        == portfolio_item.name
    )


@pytest.mark.django_db
def test_copy_portfolio_items_to_raise_exception():
    portfolio = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(portfolio=portfolio)

    with pytest.raises(RuntimeError) as excinfo:
        svc = CopyPortfolioItem(portfolio_item)
        svc.process()

    assert (
        f"{portfolio_item.name} is not order able, and cannot be copied"
        in str(excinfo.value)
    )
