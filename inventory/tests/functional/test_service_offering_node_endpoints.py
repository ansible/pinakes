""" Module to test ServiceOfferingNode end points """
import json
import pytest
from django.urls import reverse
from inventory.tests.factories import ServiceOfferingNodeFactory

@pytest.mark.django_db
def test_service_offering_node_list(api_request):
    """Test to list ServiceOfferingNode endpoint"""

    ServiceOfferingNodeFactory()
    response = api_request("get", reverse("inventory:serviceofferingnode-list"))

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1

@pytest.mark.django_db
def test_service_offering_node_retrieve(api_request):
    """Test to retrieve ServiceOfferingNode endpoint"""

    service_offering_node = ServiceOfferingNodeFactory()
    response = api_request(
        "get",
        reverse("inventory:serviceofferingnode-detail", args=(service_offering_node.id,)),
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == service_offering_node.id

@pytest.mark.django_db
def test_service_offering_node_patch_not_supported(api_request):
    """Test to patch ServiceOfferingNode endpoint"""

    service_offering_node = ServiceOfferingNodeFactory()
    response = api_request(
        "patch",
        reverse("inventory:serviceofferingnode-detail", args=(service_offering_node.id,)),
        {"name": "update"},
    )

    assert response.status_code == 405

@pytest.mark.django_db
def test_service_offering_node_delete_not_supported(api_request):
    """Test to delete ServiceOfferingNode endpoint"""

    service_offering_node = ServiceOfferingNodeFactory()
    response = api_request(
        "delete",
        reverse("inventory:serviceofferingnode-detail", args=(service_offering_node.id,)),
    )

    assert response.status_code == 405

@pytest.mark.django_db
def test_service_offering_node_put_not_supported(api_request):
    """Test to put ServiceOfferingNode endpoint"""

    service_offering_node = ServiceOfferingNodeFactory()
    response = api_request(
        "put",
        reverse("inventory:serviceofferingnode-detail", args=(service_offering_node.id,)),
        {"name": "update"},
    )

    assert response.status_code == 405
