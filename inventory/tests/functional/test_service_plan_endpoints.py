import pytest
import json
from django.urls import reverse
from inventory.tests.factories import ServicePlanFactory

@pytest.mark.django_db
class TestServicePlanEndPoints:
    def test_service_plan_list(self, api_client):
        ServicePlanFactory()
        url = reverse("inventory:serviceplan-list")
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)

        assert content["count"] == 1

    def test_service_plan_retrieve(self, api_client):
        service_plan = ServicePlanFactory()
        url = reverse("inventory:serviceplan-detail", args=(service_plan.id,))
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)
        assert content["id"] == service_plan.id

    def test_service_plan_patch_not_supported(self, api_client):
        service_plan = ServicePlanFactory()
        url = reverse("inventory:serviceplan-detail", args=(service_plan.id,))
        response = api_client.patch(url, {"name": "update"}, format="json")

        assert response.status_code == 405

    def test_service_plan_delete_not_supported(self, api_client):
        service_plan = ServicePlanFactory()
        url = reverse("inventory:serviceplan-detail", args=(service_plan.id,))
        response = api_client.delete(url)

        assert response.status_code == 405

    def test_service_plan_put_not_supported(self, api_client):
        service_plan = ServicePlanFactory()
        url = reverse("inventory:serviceplan-detail", args=(service_plan.id,))
        response = api_client.put(url, {"name": "update"}, format="json")

        assert response.status_code == 405
