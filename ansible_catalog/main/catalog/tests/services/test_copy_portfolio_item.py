"""Test copy portfolio item service"""
import pytest

from ansible_catalog.main.catalog.models import (
    CatalogServicePlan,
    PortfolioItem,
)
from ansible_catalog.main.catalog.services.copy_portfolio_item import (
    CopyPortfolioItem,
)
from ansible_catalog.main.catalog.tests.factories import (
    PortfolioFactory,
    PortfolioItemFactory,
)
from ansible_catalog.main.catalog.tests.factories import (
    ServicePlanFactory as CatalogServicePlanFactory,
)
from ansible_catalog.main.inventory.tests.factories import (
    ServiceOfferingFactory,
    ServicePlanFactory,
)


@pytest.mark.django_db
def test_portfolio_item_is_orderable_with_null_service_offering():
    portfolio = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(portfolio=portfolio)
    options = {
        "portfolio_item_name": "my test",
        "portfolio_id": portfolio.id,
    }

    svc = CopyPortfolioItem(portfolio_item, options)
    orderable = svc._is_orderable()

    assert orderable is False


@pytest.mark.django_db
def test_portfolio_item_is_orderable_with_empty_service_plans():
    service_offering = ServiceOfferingFactory()
    portfolio = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id),
        portfolio=portfolio,
    )
    options = {
        "portfolio_item_name": "my test",
    }

    svc = CopyPortfolioItem(portfolio_item, options)
    orderable = svc._is_orderable()

    assert orderable is True


@pytest.mark.django_db
def test_portfolio_item_is_orderable_with_service_plans():
    schema = {
        "schema_type": "default",
        "schema": {
            "fields": [
                {
                    "label": "Number of Job templates",
                    "name": "dev_null",
                    "initial_value": 8,
                    "helper_text": "Number of Job templates on this workflow",
                    "is_required": True,
                    "component": "text-field",
                    "type": "number",
                    "data_type": "integer",
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
    service_offering = ServiceOfferingFactory()
    ServicePlanFactory(
        create_json_schema=schema, service_offering=service_offering
    )
    portfolio = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id),
        portfolio=portfolio,
    )
    CatalogServicePlanFactory(base_schema={}, portfolio_item=portfolio_item)

    options = {
        "portfolio_item_name": "my test",
    }

    svc = CopyPortfolioItem(portfolio_item, options)
    orderable = svc._is_orderable()

    assert orderable is True


@pytest.mark.django_db
def test_process():
    schema = {
        "schema_type": "default",
        "schema": {
            "fields": [
                {
                    "label": "Number of Job templates",
                    "name": "dev_null",
                    "initial_value": 8,
                    "helper_text": "Number of Job templates on this workflow",
                    "is_required": True,
                    "component": "text-field",
                    "type": "number",
                    "data_type": "integer",
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
    service_offering = ServiceOfferingFactory()
    ServicePlanFactory(
        create_json_schema=schema, service_offering=service_offering
    )

    portfolio = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id),
        portfolio=portfolio,
    )
    CatalogServicePlanFactory(portfolio_item=portfolio_item)

    options = {
        "portfolio_item_name": portfolio_item.name,
    }

    assert PortfolioItem.objects.count() == 1
    assert CatalogServicePlan.objects.count() == 1

    svc = CopyPortfolioItem(portfolio_item, options)
    svc.process()

    assert PortfolioItem.objects.count() == 2
    assert (
        PortfolioItem.objects.last().name == "Copy of %s" % portfolio_item.name
    )
    assert portfolio_item.portfolio == PortfolioItem.objects.last().portfolio

    assert CatalogServicePlan.objects.count() == 2
    assert (
        CatalogServicePlan.objects.first().name
        == CatalogServicePlan.objects.last().name
    )
