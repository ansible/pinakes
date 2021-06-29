import pytest
import json
from django.urls import reverse
from inventory.tests.factories import ServiceInventoryFactory

@pytest.mark.django_db
class TestServiceInventoryEndPoints:
    def test_service_inventory_list(self, api_client):
        ServiceInventoryFactory()
        url = reverse("inventory:serviceinventory-list")
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)

        assert content["count"] == 1

    def test_service_inventory_retrieve(self, api_client):
        service_inventory = ServiceInventoryFactory()
        url = reverse("inventory:serviceinventory-detail", args=(service_inventory.id,))
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)
        assert content["id"] == service_inventory.id

    def test_service_inventory_tags(self, api_client):
        service_inventory = ServiceInventoryFactory()
        url = reverse("inventory:serviceinventory-tags", args=(service_inventory.id,))
        response = api_client.get(url)

        assert response.status_code == 200

    def test_service_inventory_tag(self, api_client):
        service_inventory = ServiceInventoryFactory()
        url = reverse("inventory:serviceinventory-tag", args=(service_inventory.id,))
        response = api_client.post(url, {"name": "fred"}, format="json")

        assert response.status_code == 201

    def test_service_inventory_untag(self, api_client):
        service_inventory = ServiceInventoryFactory()
        url = reverse("inventory:serviceinventory-untag", args=(service_inventory.id,))
        response = api_client.post(url, {"name": "fred"}, format="json")

        assert response.status_code == 204

    def test_service_inventory_delete_not_supported(self, api_client):
        service_inventory = ServiceInventoryFactory()
        url = reverse("inventory:serviceinventory-detail", args=(service_inventory.id,))
        response = api_client.delete(url)

        assert response.status_code == 405

    def test_service_inventory_put_not_supported(self, api_client):
        service_inventory = ServiceInventoryFactory()
        url = reverse("inventory:serviceinventory-detail", args=(service_inventory.id,))
        response = api_client.put(url, {"name": "update"}, format="json")

        assert response.status_code == 405
