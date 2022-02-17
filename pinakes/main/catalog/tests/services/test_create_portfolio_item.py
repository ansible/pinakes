"""Test create a portfolio item service"""
import pytest

from pinakes.main.catalog.exceptions import (
    BadParamsException,
)
from pinakes.main.catalog.services.create_portfolio_item import (
    CreatePortfolioItem,
)
from pinakes.main.catalog.tests.factories import (
    PortfolioFactory,
)
from pinakes.main.inventory.tests.factories import (
    ServiceOfferingFactory,
    InventoryServicePlanFactory,
)
from pinakes.main.tests.factories import (
    UserFactory,
)


@pytest.mark.django_db
def test_process_with_extra_parameters():
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    inventory_service_plan = InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema={"schemaType": "test"},
        schema_sha256="111",
    )
    portfolio = PortfolioFactory()
    user = UserFactory(first_name="Catalog", last_name="Ansible")

    options = {
        "name": "my test",
        "description": "my test description",
        "portfolio": portfolio.id,
        "service_offering_ref": str(service_offering.id),
        "user": user,
    }

    svc = CreatePortfolioItem(options).process()
    item = svc.item
    plan = svc.service_plan

    assert item.name == "my test"
    assert item.description == "my test description"
    assert item.service_offering_ref == str(service_offering.id)
    assert item.service_offering_source_ref == str(service_offering.source.id)
    assert item.portfolio == portfolio
    assert item.owner == f"{user.first_name} {user.last_name}"
    assert plan.portfolio_item == item
    assert plan.inventory_service_plan_ref == str(inventory_service_plan.id)
    assert plan.name == inventory_service_plan.name
    assert plan.id > 0


@pytest.mark.django_db
def test_process_only_with_required_parameters():
    service_offering = ServiceOfferingFactory()
    portfolio = PortfolioFactory()
    user = UserFactory(first_name="Catalog", last_name="Ansible")

    options = {
        "portfolio": portfolio.id,
        "service_offering_ref": str(service_offering.id),
        "user": user,
    }

    svc = CreatePortfolioItem(options)
    item = svc.process().item

    assert item.name == service_offering.name
    assert item.service_offering_ref == str(service_offering.id)
    assert item.service_offering_source_ref == str(service_offering.source.id)
    assert item.portfolio == portfolio
    assert item.owner == f"{user.first_name} {user.last_name}"


@pytest.mark.django_db
def test_process_with_invalid_service_offering():
    portfolio = PortfolioFactory()
    options = {
        "portfolio": portfolio.id,
        "service_offering_ref": "abc",
    }

    with pytest.raises(BadParamsException) as excinfo:
        CreatePortfolioItem(options).process()

    assert "Failed to get service offering" in str(excinfo.value)
