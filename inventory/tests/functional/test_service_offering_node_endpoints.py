import pytest
import json
from django.urls import reverse
from inventory.tests.factories import ServiceOfferingNodeFactory

@pytest.mark.django_db
class TestServiceOfferingNodeEndPoints:
    def test_service_offering_node_list(self, api_client):
        ServiceOfferingNodeFactory()
        url = reverse("inventory:serviceofferingnode-list")
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)

        assert content["count"] == 1

    def test_service_offering_node_retrieve(self, api_client):
        service_offering_node = ServiceOfferingNodeFactory()
        url = reverse("inventory:serviceofferingnode-detail", args=(service_offering_node.id,))
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)
        assert content["id"] == service_offering_node.id

    def test_service_offering_node_patch_not_supported(self, api_client):
        service_offering_node = ServiceOfferingNodeFactory()
        url = reverse("inventory:serviceofferingnode-detail", args=(service_offering_node.id,))
        response = api_client.patch(url, {"name": "update"}, format="json")

        assert response.status_code == 405

    def test_service_offering_node_delete_not_supported(self, api_client):
        service_offering_node = ServiceOfferingNodeFactory()
        url = reverse("inventory:serviceofferingnode-detail", args=(service_offering_node.id,))
        response = api_client.delete(url)

        assert response.status_code == 405

    def test_service_offering_node_put_not_supported(self, api_client):
        service_offering_node = ServiceOfferingNodeFactory()
        url = reverse("inventory:serviceofferingnode-detail", args=(service_offering_node.id,))
        response = api_client.put(url, {"name": "update"}, format="json")

        assert response.status_code == 405
