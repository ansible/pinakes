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
    portfolio_item = PortfolioItemFactory()
    service_plan = ServicePlanFactory(
        portfolio_item=portfolio_item,
        service_offering_ref=portfolio_item.service_offering_ref,
        base_schema=TEST_SCHEMA,
        base_sha256=TEST_SHA256,
    )

    response = api_request(
        "get", "serviceplan-detail", service_plan.id, {"extra": True}
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["schema"] == TEST_SCHEMA
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
def test_service_plan_reset_post_another_base(api_request):
    """Reset the service plan by id"""
    _test_service_plan_reset(api_request, {"schemaType": "base"}, "xyz123")


@pytest.mark.django_db
def test_service_plan_reset_post_same_base(api_request):
    """Reset the service plan by id"""
    _test_service_plan_reset(api_request, TEST_SCHEMA, TEST_SHA256)


def _test_service_plan_reset(api_request, remote_schema, remote_sha):
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    remote_service_plan = InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=remote_schema,
        schema_sha256=remote_sha,
    )

    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )

    catalog_service_plan = ServicePlanFactory(
        portfolio_item=portfolio_item,
        service_offering_ref=portfolio_item.service_offering_ref,
        base_schema=TEST_SCHEMA,
        modified_schema={"schemaType": "modified"},
        outdated=True,
        outdated_changes="message",
        base_sha256=TEST_SHA256,
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

    catalog_service_plan.refresh_from_db()
    assert (
        catalog_service_plan.schema == remote_service_plan.create_json_schema
    )
    assert catalog_service_plan.modified is False
    assert catalog_service_plan.outdated is False
    assert catalog_service_plan.outdated_changes == ""
    assert (
        catalog_service_plan.base_sha256 == remote_service_plan.schema_sha256
    )
