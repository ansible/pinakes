""" Test service_plan end points """
import json
import pytest

from ansible_catalog.main.catalog.tests.factories import (
    PortfolioItemFactory,
    ServicePlanFactory,
)
from ansible_catalog.main.inventory.tests.factories import (
    ServiceOfferingFactory,
)
from ansible_catalog.main.inventory.tests.factories import (
    ServicePlanFactory as InventoryServicePlanFactory,
)


@pytest.mark.django_db
def test_portfolio_item_service_plan_get(api_request):
    """List CatalogServicePlan by PortfolioItem id"""
    portfolio_item = PortfolioItemFactory()

    service_plan = ServicePlanFactory(portfolio_item=portfolio_item)

    response = api_request(
        "get", "portfolioitem-serviceplan-list", portfolio_item.id
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1
    assert content["results"][0]["service_plan_ref"] == str(service_plan.id)
    assert content["results"][0]["portfolio_item"] == portfolio_item.id


@pytest.mark.django_db
def test_service_plan_base_retrieve(api_request):
    """Retrieve the base schema for a service plan by id"""
    portfolio_item = PortfolioItemFactory()

    service_plan = ServicePlanFactory(portfolio_item=portfolio_item)
    response = api_request(
        "get", reverse("catalogserviceplan-base", args=(service_plan.id,))
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["name"] == service_plan.name
    assert content["service_plan_ref"] == str(service_plan.id)
    assert content["portfolio_item"] == portfolio_item.id


@pytest.mark.django_db
def test_service_plan_modified_retrieve_without_schema(api_request):
    """Retrieve the modified schema for a service plan by id"""
    portfolio_item = PortfolioItemFactory()

    service_plan = ServicePlanFactory(portfolio_item=portfolio_item)
    response = api_request(
        "get", reverse("catalogserviceplan-modified", args=(service_plan.id,))
    )

    assert response.status_code == 204


@pytest.mark.django_db
def test_service_plan_modified_retrieve_with_schema(api_request):
    """Retrieve the modified schema for a service plan by id"""
    portfolio_item = PortfolioItemFactory()

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

    service_plan = ServicePlanFactory(
        portfolio_item=portfolio_item, modified_schema=schema
    )
    response = api_request(
        "get", reverse("catalogserviceplan-modified", args=(service_plan.id,))
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["name"] == service_plan.name
    assert content["create_json_schema"] == schema
    assert content["service_plan_ref"] == str(service_plan.id)
    assert content["portfolio_item"] == portfolio_item.id


@pytest.mark.django_db
def test_service_plan_modified_patch(api_request):
    """Update the modified schema for a service plan by id"""
    portfolio_item = PortfolioItemFactory()
    service_plan = ServicePlanFactory(portfolio_item=portfolio_item)
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

    data = {"modified": schema}
    response = api_request(
        "patch",
        reverse(
            "catalogserviceplan-modified",
            args=(service_plan.id,),
        ),
        data,
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content == schema


@pytest.mark.django_db
def test_service_plan_reset_post_with_ok_status(api_request):
    """Reset the service plan by id"""
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    inventory_service_plan = InventoryServicePlanFactory(
        service_offering=service_offering
    )

    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )
    catalog_service_plan = ServicePlanFactory(portfolio_item=portfolio_item)

    response = api_request(
        "post",
        reverse("catalogserviceplan-reset", args=(catalog_service_plan.id,)),
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["name"] == inventory_service_plan.name
    assert content["portfolio_item"] == portfolio_item.id
    assert content["imported"] is True
    assert content["modified"] is False


@pytest.mark.django_db
def test_service_plan_reset_post_without_content_status(api_request):
    """Reset the service plan by id"""
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    InventoryServicePlanFactory(service_offering=service_offering)

    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )
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

    catalog_service_plan = ServicePlanFactory(
        portfolio_item=portfolio_item, modified_schema=schema
    )

    response = api_request(
        "post",
        reverse("catalogserviceplan-reset", args=(catalog_service_plan.id,)),
    )

    assert response.status_code == 204


@pytest.mark.django_db
def test_service_plan_retrieve(api_request):
    """Retrieve a single service plan by id"""
    portfolio_item = PortfolioItemFactory()

    service_plan = ServicePlanFactory(portfolio_item=portfolio_item)
    response = api_request(
        "get", reverse("catalogserviceplan-detail", args=(service_plan.id,))
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["name"] == service_plan.name


@pytest.mark.django_db
def test_service_plan_post(api_request):
    """Create a CatalogServicePlan"""

    service_offering = ServiceOfferingFactory(survey_enabled=True)
    InventoryServicePlanFactory(service_offering=service_offering)

    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )
    data = {"portfolio_item_id": portfolio_item.id}
    response = api_request("post", reverse("catalogserviceplan-list"), data)

    assert response.status_code == 201
