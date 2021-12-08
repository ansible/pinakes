""" Test service_plan end points """
import json
import pytest
import copy

from ansible_catalog.main.catalog.tests.factories import (
    PortfolioItemFactory,
    CatalogServicePlanFactory,
)
from ansible_catalog.main.inventory.tests.factories import (
    ServiceOfferingFactory,
)
from ansible_catalog.main.inventory.tests.factories import (
    InventoryServicePlanFactory,
)

TEST_SCHEMA = {
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


@pytest.mark.django_db
def test_portfolio_item_service_plan_get_local(api_request):
    """List CatalogServicePlan by PortfolioItem id"""
    portfolio_item = PortfolioItemFactory()

    service_plan = CatalogServicePlanFactory(
        portfolio_item=portfolio_item, service_plan_ref="abc"
    )

    response = api_request(
        "get", "portfolioitem-serviceplan-list", portfolio_item.id
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content[0]["service_plan_ref"] == service_plan.service_plan_ref
    assert content[0]["portfolio_item"] == portfolio_item.id
    assert content[0]["id"] is not None
    assert content[0]["extra_data"] is None


@pytest.mark.django_db
def test_portfolio_item_service_plan_get_remote(api_request):
    """List CatalogServicePlan by PortfolioItem id"""
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    inventory_service_plan = InventoryServicePlanFactory(
        service_offering=service_offering
    )

    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )

    response = api_request(
        "get",
        "portfolioitem-serviceplan-list",
        portfolio_item.id,
        {"extra": True},
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content[0]["service_plan_ref"] == str(inventory_service_plan.id)
    assert content[0]["portfolio_item"] == portfolio_item.id
    assert content[0]["id"] is None
    assert content[0]["extra_data"] is not None


@pytest.mark.django_db
def test_service_plan_retrieve(api_request):
    """Retrieve the schema that was not modified"""
    portfolio_item = PortfolioItemFactory()

    service_plan = CatalogServicePlanFactory(
        portfolio_item=portfolio_item,
        service_plan_ref="abc",
        base_schema=TEST_SCHEMA,
    )
    response = api_request(
        "get", "catalogserviceplan-detail", service_plan.id, {"extra": True}
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["name"] == service_plan.name
    assert content["schema"] == TEST_SCHEMA
    assert content["service_plan_ref"] == service_plan.service_plan_ref
    assert content["portfolio_item"] == portfolio_item.id
    assert content["extra_data"]["base_schema"] == TEST_SCHEMA


@pytest.mark.django_db
def test_service_plan_retrieve_without_schema(api_request):
    """Retrieve the modified schema for a service plan by id"""
    portfolio_item = PortfolioItemFactory()

    service_plan = CatalogServicePlanFactory(portfolio_item=portfolio_item)
    response = api_request(
        "get",
        "catalogserviceplan-detail",
        service_plan.id,
        {"extra": True},
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["schema"] is None
    assert content["extra_data"]["base_schema"] is None


@pytest.mark.django_db
def test_service_plan_retrieve_with_modified_schema(api_request):
    """Retrieve the modified schema for a service plan by id"""
    portfolio_item = PortfolioItemFactory()

    modified_schema = copy.deepcopy(TEST_SCHEMA)
    modified_schema["schema"]["fields"][0]["initial_value"] = 10

    service_plan = CatalogServicePlanFactory(
        portfolio_item=portfolio_item,
        base_schema=TEST_SCHEMA,
        modified_schema=modified_schema,
        service_plan_ref="abc",
    )
    response = api_request(
        "get", "catalogserviceplan-detail", service_plan.id, {"extra": True}
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["name"] == service_plan.name
    assert content["schema"] == modified_schema
    assert content["service_plan_ref"] == service_plan.service_plan_ref
    assert content["portfolio_item"] == portfolio_item.id
    assert content["extra_data"]["base_schema"] == TEST_SCHEMA


@pytest.mark.django_db
def test_service_plan_patch(api_request):
    """Update the modified schema for a service plan by id"""
    portfolio_item = PortfolioItemFactory()
    service_plan = CatalogServicePlanFactory(portfolio_item=portfolio_item)

    assert service_plan.modified_schema is None
    assert service_plan.modified is False

    response = api_request(
        "patch",
        "catalogserviceplan-detail",
        service_plan.id,
        {"modified": TEST_SCHEMA},
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["schema"] == TEST_SCHEMA
    assert content["modified"] is True

    service_plan.refresh_from_db()
    assert service_plan.modified_schema == TEST_SCHEMA


@pytest.mark.django_db
def test_service_plan_reset_post(api_request):
    """Reset the service plan by id"""
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    remote_service_plan = InventoryServicePlanFactory(
        service_offering=service_offering
    )

    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )

    catalog_service_plan = CatalogServicePlanFactory(
        portfolio_item=portfolio_item, modified_schema=TEST_SCHEMA
    )

    response = api_request(
        "post",
        "catalogserviceplan-reset",
        catalog_service_plan.id,
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["schema"] == remote_service_plan.create_json_schema


@pytest.mark.django_db
def test_service_plan_post(api_request):
    """Create/Import a CatalogServicePlan"""

    service_offering = ServiceOfferingFactory(survey_enabled=True)
    InventoryServicePlanFactory(service_offering=service_offering)

    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )

    response = api_request(
        "post",
        "portfolioitem-serviceplan-list",
        portfolio_item.id,
    )
    assert response.status_code == 201
    content = json.loads(response.content)
    assert content["imported"] is True

    response = api_request(
        "post",
        "portfolioitem-serviceplan-list",
        portfolio_item.id,
    )
    assert response.status_code == 400
