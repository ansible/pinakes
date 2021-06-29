import pytest
import json
from django.urls import reverse
from inventory.tests.factories import (
    ServicePlanFactory,
    ServiceOfferingFactory,
    ServiceOfferingNodeFactory
)


@pytest.mark.django_db
class TestServiceOfferingEndPoints:
    def test_service_offering_list(self, api_client):
        ServiceOfferingFactory()
        url = reverse("inventory:serviceoffering-list")
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)

        assert content["count"] == 1

    def test_service_offering_retrieve(self, api_client):
        service_offering = ServiceOfferingFactory()
        url = reverse("inventory:serviceoffering-detail", args=(service_offering.id,))
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)
        assert content["id"] == service_offering.id

    def test_service_offering_patch_not_supported(self, api_client):
        service_offering = ServiceOfferingFactory()
        url = reverse("inventory:serviceoffering-detail", args=(service_offering.id,))
        response = api_client.patch(url, {"name": "update"}, format="json")

        assert response.status_code == 405

    def test_service_offering_delete_not_supported(self, api_client):
        service_offering = ServiceOfferingFactory()
        url = reverse("inventory:serviceoffering-detail", args=(service_offering.id,))
        response = api_client.delete(url)

        assert response.status_code == 405

    def test_service_offering_put_not_supported(self, api_client):
        service_offering = ServiceOfferingFactory()
        url = reverse("inventory:serviceoffering-detail", args=(service_offering.id,))
        response = api_client.put(url, {"name": "update"}, format="json")

        assert response.status_code == 405

    def test_service_offering_service_offering_node_list(self, api_client):
        service_offering = ServiceOfferingFactory()
        service_offering_node = ServiceOfferingNodeFactory(service_offering=service_offering)
        url = reverse("inventory:offering-nodes-list", args=(service_offering.id,))
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)

        assert content["count"] == 1

    def test_service_offering_service_plan_list(self, api_client):
        service_offering = ServiceOfferingFactory()
        service_plan = ServicePlanFactory(service_offering=service_offering)
        url = reverse("inventory:offering-service_plans-list", args=(service_offering.id,))
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)

        assert content["count"] == 1
