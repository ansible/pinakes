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
class TestSourceEndPoints:
    def test_source_list(self, api_client):
        SourceFactory()
        url = reverse("inventory:source-list")
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)

        assert content["count"] == 1

    def test_source_retrieve(self, api_client):
        source = SourceFactory()
        url = reverse("inventory:source-detail", args=(source.id,))
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)
        assert content["id"] == source.id

    def test_source_refresh(self, api_client):
        source = SourceFactory()
        url = reverse("inventory:source-refresh", args=(source.id,))
        response = api_client.patch(url)

        assert response.status_code == 204

    def test_source_patch(self, api_client):
        source = SourceFactory()
        url = reverse("inventory:source-detail", args=(source.id,))
        response = api_client.patch(url, {"name": "update"}, format="json")

        assert response.status_code == 200

    def test_source_delete_not_supported(self, api_client):
        source = SourceFactory()
        url = reverse("inventory:source-detail", args=(source.id,))
        response = api_client.delete(url)

        assert response.status_code == 405

    def test_source_put_not_supported(self, api_client):
        source = SourceFactory()
        url = reverse("inventory:source-detail", args=(source.id,))
        response = api_client.put(url, {"name": "update"}, format="json")

        assert response.status_code == 405

    def test_source_service_inventory_list(self, api_client):
        source = SourceFactory()
        service_inventory = ServiceInventoryFactory(source=source)
        url = reverse("inventory:source-service_inventory-list", args=(source.id,))
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)

        assert content["count"] == 1

    def test_source_service_plan_list(self, api_client):
        source = SourceFactory()
        service_plan = ServicePlanFactory(source=source)
        url = reverse("inventory:source-service_plan-list", args=(source.id,))
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)

        assert content["count"] == 1

    def test_source_service_offering_list(self, api_client):
        source = SourceFactory()
        service_offering = ServiceOfferingFactory(source=source)
        url = reverse("inventory:source-service_offering-list", args=(source.id,))
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)

        assert content["count"] == 1

    def test_source_service_offering_node_list(self, api_client):
        source = SourceFactory()
        service_offering_node = ServiceOfferingNodeFactory(source=source)
        url = reverse("inventory:source-service_offering_node-list", args=(source.id,))
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)

        assert content["count"] == 1

