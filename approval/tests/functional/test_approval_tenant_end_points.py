""" Tenant Test module """
import json
import pytest
from django.urls import reverse
from approval.tests.factories import TenantFactory


@pytest.mark.django_db
def test_tenant_list(api_request):
    """GET a list of Tenants"""
    TenantFactory()
    url = reverse("approval:tenant-list")
    response = api_request("get", url)

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1


@pytest.mark.django_db
def test_tenant_retrieve(api_request):
    """RETRIEVE a tenant based on id"""
    tenant = TenantFactory()
    url = reverse("approval:tenant-detail", args=(tenant.id,))
    response = api_request("get", url)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == tenant.id


@pytest.mark.django_db
def test_tenant_delete_fail(api_request):
    """DELETE should fail on tenant"""
    tenant = TenantFactory()
    url = reverse("approval:tenant-detail", args=(tenant.id,))
    response = api_request("delete", url)

    assert response.status_code == 405


@pytest.mark.django_db
def test_tenant_patch_fail(api_request):
    """PUT should fail on tenant"""
    tenant = TenantFactory()
    url = reverse("approval:tenant-detail", args=(tenant.id,))
    response = api_request("put", url, {"external_tenant": "update"})

    assert response.status_code == 405


@pytest.mark.django_db
def test_tenant_post_fail(api_request):
    """Post should fail on tenant"""
    TenantFactory()
    url = reverse("approval:tenant-list")
    response = api_request("post", url, {"external_tenant": "abcdef"})

    assert response.status_code == 405
