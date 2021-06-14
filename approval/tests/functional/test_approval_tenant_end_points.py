import pytest
import json
from django.urls import reverse
from approval.tests.factories import TenantFactory


@pytest.mark.django_db
class TestTenantEndPoints:
    def test_tenant_list(self, api_client):
        TenantFactory()
        url = reverse("approval:tenant-list")
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)

        assert content["count"] == 1

    def test_tenant_retrieve(self, api_client):
        tenant = TenantFactory()
        url = reverse("approval:tenant-detail", args=(tenant.id,))
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)
        assert content["id"] == tenant.id

    def test_tenant_delete_fail(self, api_client):
        tenant = TenantFactory()
        url = reverse("approval:tenant-detail", args=(tenant.id,))
        response = api_client.delete(url)

        assert response.status_code == 405

    def test_tenant_patch_fail(self, api_client):
        tenant = TenantFactory()
        url = reverse("approval:tenant-detail", args=(tenant.id,))
        response = api_client.put(url, {"external_tenant": "update"}, format="json")

        assert response.status_code == 405

    def test_tenant_post_fail(self, api_client):
        tenant = TenantFactory()
        url = reverse("approval:tenant-list")
        response = api_client.post(url, {"external_tenant": "abcdef"}, format="json")

        assert response.status_code == 405
