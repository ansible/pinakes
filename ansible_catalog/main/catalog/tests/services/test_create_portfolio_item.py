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
)


@pytest.mark.django_db
def test_process_with_extra_parameters():
    service_offering = ServiceOfferingFactory()
    portfolio = PortfolioFactory()
    options = {
        "name": "my test",
        "description": "my test description",
        "portfolio": portfolio.id,
        "service_offering_ref": str(service_offering.id),
    }

    svc = CreatePortfolioItem(options)
    item = svc.process().item

    assert item.name == "my test"
    assert item.description == "my test description"
    assert item.service_offering_ref == str(service_offering.id)
    assert item.service_offering_source_ref == str(service_offering.source.id)
    assert item.portfolio == portfolio


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
