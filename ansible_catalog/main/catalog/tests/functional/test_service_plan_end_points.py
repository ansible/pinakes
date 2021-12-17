""" Test service_plan end points """
import json
import pytest
import copy

from ansible_catalog.main.catalog.tests.factories import (
    PortfolioItemFactory,
    make_service_plan,
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
TEST_SHA256 = "abc123"


@pytest.mark.django_db
def test_list_portfolio_item_service_plans(api_request):
    """List ServicePlan by PortfolioItem id"""
    service_plan = make_service_plan(TEST_SCHEMA)

    response = api_request(
        "get",
        "portfolioitem-serviceplan-list",
        service_plan.portfolio_item.id,
        {"extra": True},
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert (
        content[0]["inventory_service_plan_ref"]
        == service_plan.inventory_service_plan_ref
    )
    assert content[0]["portfolio_item"] == service_plan.portfolio_item.id
    assert content[0]["schema"] == TEST_SCHEMA
    assert content[0]["extra_data"] is not None


@pytest.mark.django_db
def test_service_plan_retrieve(api_request):
    """Retrieve a service plan by id"""
    service_plan = make_service_plan(TEST_SCHEMA)
    response = api_request(
        "get", "serviceplan-detail", service_plan.id, {"extra": True}
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["name"] == service_plan.name
    assert content["schema"] == TEST_SCHEMA
    assert (
        content["inventory_service_plan_ref"]
        == service_plan.inventory_service_plan_ref
    )
    assert content["portfolio_item"] == service_plan.portfolio_item.id
    assert content["extra_data"]["base_schema"] == TEST_SCHEMA


@pytest.mark.django_db
def test_service_plan_patch(api_request):
    """Update the modified schema for a service plan by id"""
    service_plan = make_service_plan()

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
    service_plan = make_service_plan(TEST_SCHEMA)
    service_plan.base_schema = {"schema": "old"}
    service_plan.base_sha256 = "123"
    service_plan.modified_schema = {"schema": "modified"}
    service_plan.save()

    assert service_plan.modified is True
    assert service_plan.outdated is True
    assert len(service_plan.outdated_changes) > 0

    response = api_request(
        "post",
        "serviceplan-reset",
        service_plan.id,
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["schema"] == TEST_SCHEMA
    assert content["modified"] is False
    assert content["outdated"] is False
    assert content["outdated_changes"] == ""
