""" Test service_plan end points """
import json

from unittest.mock import patch
import pytest
import copy

from ansible_catalog.main.catalog.tests.factories import (
    PortfolioItemFactory,
    ServicePlanFactory,
)
from ansible_catalog.main.inventory.tests.factories import (
    ServiceOfferingFactory,
)
from ansible_catalog.main.inventory.tests.factories import (
    InventoryServicePlanFactory,
)

TEST_SCHEMA = {
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
TEST_SHA256 = "abc123"


@pytest.mark.django_db
def test_list_portfolio_item_service_plans(api_request):
    """List ServicePlan by PortfolioItem id"""
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    inventory_service_plan = InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=TEST_SCHEMA,
        schema_sha256=TEST_SHA256,
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

    assert content[0]["inventory_service_plan_ref"] == str(
        inventory_service_plan.id
    )
    assert content[0]["portfolio_item"] == portfolio_item.id
    assert content[0]["schema"] == TEST_SCHEMA
    assert content[0]["extra_data"] is not None


@pytest.mark.django_db
def test_service_plan_retrieve(api_request):
    """Retrieve a service plan by id"""
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    inventory_service_plan = InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=TEST_SCHEMA,
        schema_sha256=TEST_SHA256,
    )

    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )
    service_plan = ServicePlanFactory(
        portfolio_item=portfolio_item,
        service_offering_ref=portfolio_item.service_offering_ref,
    )

    response = api_request(
        "get", "serviceplan-detail", service_plan.id, {"extra": True}
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["name"] == inventory_service_plan.name
    assert content["schema"] == TEST_SCHEMA
    assert content["inventory_service_plan_ref"] == str(
        inventory_service_plan.id
    )
    assert content["portfolio_item"] == portfolio_item.id
    assert content["extra_data"]["base_schema"] == TEST_SCHEMA


@pytest.mark.django_db
def test_service_plan_patch(api_request):
    """Update the modified schema for a service plan by id"""
    base_schema = {"schemaType": "base"}
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    inventory_service_plan = InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=base_schema,
        schema_sha256=TEST_SHA256,
    )

    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )
    service_plan = ServicePlanFactory(
        portfolio_item=portfolio_item,
        service_offering_ref=portfolio_item.service_offering_ref,
        base_schema=base_schema,
        base_sha256="xyz123",
    )

    assert service_plan.modified_schema is None
    assert service_plan.modified is False

    response = api_request(
        "patch",
        "serviceplan-detail",
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
        service_offering=service_offering,
        create_json_schema={"schemaType": "base"},
        schema_sha256="xyz123",
    )

    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )

    catalog_service_plan = ServicePlanFactory(
        portfolio_item=portfolio_item,
        service_offering_ref=portfolio_item.service_offering_ref,
        modified_schema=TEST_SCHEMA,
        outdated=True,
        outdated_changes="message",
    )

    response = api_request(
        "post",
        "serviceplan-reset",
        catalog_service_plan.id,
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["schema"] == remote_service_plan.create_json_schema
    assert content["modified"] is False
    assert content["outdated"] is False
    assert content["outdated_changes"] == ""


@pytest.mark.django_db
def test_service_plan_retrieve(api_request, mocker):
    """Retrieve a single service plan by id"""
    portfolio_item = PortfolioItemFactory()

    service_plan = ServicePlanFactory(portfolio_item=portfolio_item)

    with patch(
        "ansible_catalog.main.catalog.services.compare_service_plans.CompareServicePlans.is_changed"
    ) as mock:
        mock.return_value = False

        response = api_request(
            "get",
            "catalogserviceplan-detail",
            service_plan.id,
        )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["name"] == service_plan.name


@pytest.mark.django_db
def test_service_plan_retrieve_with_changed_survey(api_request):
    """Retrieve a single service plan by id"""

    schema1 = {
        "schemaType": "default",
        "schema": {
            "fields": [
                {
                    "label": "State",
                    "name": "state",
                    "initial_value": "",
                    "helper_text": "The state where you live",
                    "is_required": True,
                    "component": "select-field",
                    "options": [
                        {"label": "NJ", "value": "NJ"},
                        {"label": "PA", "value": "PA"},
                        {"label": "OK", "value": "OK"},
                    ],
                    "validate": [{"type": "required-validator"}],
                }
            ],
            "title": "",
            "description": "",
        },
    }

    schema2 = {
        "schemaType": "default",
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

    service_offering = ServiceOfferingFactory(survey_enabled=True)
    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )

    InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=schema2,
    )
    service_plan = ServicePlanFactory(
        portfolio_item=portfolio_item, base_schema=schema1
    )

    response = api_request(
        "get",
        "catalogserviceplan-detail",
        service_plan.id,
    )

    assert response.status_code == 400
    content = json.loads(response.content)
    assert content[
        "detail"
    ] == "The underlying survey on %s in the %s portfolio has been changed and is no longer valid, please contact an administrator to fix it." % (
        portfolio_item.name,
        portfolio_item.portfolio.name,
    )


@pytest.mark.django_db
def test_service_plan_post(api_request):
    """Create a CatalogServicePlan"""

    service_offering = ServiceOfferingFactory(survey_enabled=True)
    InventoryServicePlanFactory(service_offering=service_offering)

    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )
    data = {"portfolio_item_id": portfolio_item.id}
    response = api_request(
        "post",
        "catalogserviceplan-list",
        data=data,
    )

    assert response.status_code == 201
