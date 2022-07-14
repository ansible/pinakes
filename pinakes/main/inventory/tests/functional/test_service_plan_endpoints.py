"""Module to test ServicePlan end points"""
import json
import pytest
from pinakes.main.inventory.tests.factories import (
    InventoryServicePlanFactory,
)


@pytest.mark.django_db
def test_service_plan_list(api_request):
    """Test to list ServicePlan endpoint"""

    InventoryServicePlanFactory()
    response = api_request("get", "inventory:inventoryserviceplan-list")

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1


@pytest.mark.django_db
def test_service_plan_retrieve(api_request):
    """Test to retrieve ServicePlan endpoint"""

    service_plan = InventoryServicePlanFactory()
    response = api_request(
        "get", "inventory:inventoryserviceplan-detail", service_plan.id
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == service_plan.id


@pytest.mark.django_db
def test_service_plan_patch_not_supported(api_request):
    """Test to patch ServicePlan endpoint"""

    service_plan = InventoryServicePlanFactory()
    response = api_request(
        "patch",
        "inventory:inventoryserviceplan-detail",
        service_plan.id,
        {"name": "update"},
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_service_plan_delete_not_supported(api_request):
    """Test to delete ServicePlan endpoint"""

    service_plan = InventoryServicePlanFactory()
    response = api_request(
        "delete", "inventory:inventoryserviceplan-detail", service_plan.id
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_service_plan_put_not_supported(api_request):
    """Test to put ServicePlan endpoint"""

    service_plan = InventoryServicePlanFactory()
    response = api_request(
        "put",
        "inventory:inventoryserviceplan-detail",
        service_plan.id,
        {"name": "update"},
    )

    assert response.status_code == 405
