"""Module to test ServiceInventory end points"""
import json
import pytest

from pinakes.main.inventory.tests.factories import (
    ServiceInventoryFactory,
)


@pytest.mark.django_db
def test_service_inventory_list(api_request):
    """Test to list ServiceInventory endpoint"""

    ServiceInventoryFactory()
    response = api_request("get", "inventory:serviceinventory-list")

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1


@pytest.mark.django_db
def test_service_inventory_retrieve(api_request):
    """Test to retrieve ServiceInventory endpoint"""

    service_inventory = ServiceInventoryFactory(name="fred")
    response = api_request(
        "get", "inventory:serviceinventory-detail", service_inventory.id
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == service_inventory.id
    assert content["name"] == service_inventory.name


@pytest.mark.django_db
def test_service_inventory_tags(api_request):
    """Test to list ServiceInventory Tags endpoint"""

    service_inventory = ServiceInventoryFactory()
    response = api_request(
        "get", "inventory:serviceinventory-tags", service_inventory.id
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_service_inventory_tag(api_request):
    """Test to create ServiceInventory Tag endpoint"""

    service_inventory = ServiceInventoryFactory()
    response = api_request(
        "post",
        "inventory:serviceinventory-tag",
        service_inventory.id,
        {"name": "fred"},
    )

    assert response.status_code == 201


@pytest.mark.django_db
def test_service_inventory_untag(api_request):
    """Test to remove ServiceInventory Tag endpoint"""

    service_inventory = ServiceInventoryFactory()
    response = api_request(
        "post",
        "inventory:serviceinventory-untag",
        service_inventory.id,
        {"name": "fred"},
    )

    assert response.status_code == 204


@pytest.mark.django_db
def test_service_inventory_delete_not_supported(api_request):
    """Test to delete ServiceInventory endpoint"""

    service_inventory = ServiceInventoryFactory()
    response = api_request(
        "delete",
        "inventory:serviceinventory-detail",
        service_inventory.id,
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_service_inventory_put_not_supported(api_request):
    """Test to put ServiceInventory endpoint"""

    service_inventory = ServiceInventoryFactory()
    response = api_request(
        "put",
        "inventory:serviceinventory-detail",
        service_inventory.id,
        {"name": "update"},
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_service_inventory_post_not_supported(api_request):
    """Test to post ServiceInventory endpoint"""

    response = api_request(
        "post",
        "inventory:serviceinventory-list",
        data={"name": "update"},
    )

    assert response.status_code == 405
