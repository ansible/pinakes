"""Module to test ServiceInstance end points"""
import json
import pytest
from pinakes.main.inventory.tests.factories import (
    ServiceInstanceFactory,
)


@pytest.mark.django_db
def test_service_instance_list(api_request):
    """Test to list ServiceInstance endpoint"""

    ServiceInstanceFactory()
    response = api_request("get", "inventory:serviceinstance-list")

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1


@pytest.mark.django_db
def test_service_instance_retrieve(api_request):
    """Test to retrieve ServiceInstance endpoint"""

    service_instance = ServiceInstanceFactory()
    response = api_request(
        "get",
        "inventory:serviceinstance-detail",
        service_instance.id,
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == service_instance.id
    assert content["name"] == service_instance.name
    assert content["service_offering"] == service_instance.service_offering.id
    assert content["service_plan"] == service_instance.service_plan.id


@pytest.mark.django_db
def test_service_instance_patch_not_supported(api_request):
    """Test to patch ServiceInstance endpoint"""

    service_instance = ServiceInstanceFactory()
    response = api_request(
        "patch",
        "inventory:serviceinstance-detail",
        service_instance.id,
        {"name": "update"},
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_service_instance_delete_not_supported(api_request):
    """Test to delete ServiceInstance endpoint"""

    service_instance = ServiceInstanceFactory()
    response = api_request(
        "delete",
        "inventory:serviceinstance-detail",
        service_instance.id,
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_service_instance_put_not_supported(api_request):
    """Test to put ServiceInstance endpoint"""

    service_instance = ServiceInstanceFactory()
    response = api_request(
        "put",
        "inventory:serviceinstance-detail",
        service_instance.id,
        {"name": "update"},
    )

    assert response.status_code == 405
