""" Module to test Source end points """
import pytest
import json
from django.urls import reverse
from inventory.tests.factories import (
    SourceFactory,
    ServiceInventoryFactory,
    ServicePlanFactory,
    ServiceOfferingFactory,
    ServiceOfferingNodeFactory
)


@pytest.mark.django_db
def test_source_list(api_request):
    """Test to list Source endpoint"""

    SourceFactory()
    response = api_request("get", reverse("inventory:source-list"))

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1

@pytest.mark.django_db
def test_source_retrieve(api_request):
    """Test to retrieve Source endpoint"""

    source = SourceFactory()
    response = api_request(
        "get",
        reverse("inventory:source-detail", args=(source.id,)),
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == source.id

@pytest.mark.django_db
def test_source_refresh(api_request):
    """Test to refresh Source endpoint"""

    source = SourceFactory()
    response = api_request(
        "patch",
        reverse("inventory:source-refresh", args=(source.id,)),
    )

    assert response.status_code == 204

@pytest.mark.django_db
def test_source_patch(api_request):
    """Test to patch Source endpoint"""

    source = SourceFactory()
    response = api_request(
        "patch",
        reverse("inventory:source-detail", args=(source.id,)),
        {"name": "update"},
    )

    assert response.status_code == 200

@pytest.mark.django_db
def test_source_delete_not_supported(api_request):
    """Test to delete Source endpoint"""

    source = SourceFactory()
    response = api_request(
        "delete",
        reverse("inventory:source-detail", args=(source.id,)),
    )

    assert response.status_code == 405

@pytest.mark.django_db
def test_source_put_not_supported(api_request):
    """Test to put Source endpoint"""

    source = SourceFactory()
    response = api_request(
        "put",
        reverse("inventory:source-detail", args=(source.id,)),
        {"name": "update"},
    )

    assert response.status_code == 405

@pytest.mark.django_db
def test_source_service_inventory_list(api_request):
    """Test to list ServiceInventories by a certain Source endpoint"""

    source = SourceFactory()
    ServiceInventoryFactory(source=source)
    response = api_request(
        "get",
        reverse("inventory:source-service_inventory-list", args=(source.id,)),
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1

@pytest.mark.django_db
def test_source_service_plan_list(api_request):
    """Test to list ServicePlans by a certain Source endpoint"""

    source = SourceFactory()
    ServicePlanFactory(source=source)
    response = api_request(
        "get",
        reverse("inventory:source-service_plan-list", args=(source.id,)),
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1

@pytest.mark.django_db
def test_source_service_offering_list(api_request):
    """Test to list ServiceOfferings by a certain Source endpoint"""

    source = SourceFactory()
    ServiceOfferingFactory(source=source)
    response = api_request(
        "get",
        reverse("inventory:source-service_offering-list", args=(source.id,)),
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1

@pytest.mark.django_db
def test_source_service_offering_node_list(api_request):
    """Test to list ServiceOfferingNodes by a certain Source endpoint"""

    source = SourceFactory()
    ServiceOfferingNodeFactory(source=source)
    response = api_request(
        "get",
        reverse("inventory:source-service_offering_node-list", args=(source.id,)),
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1
