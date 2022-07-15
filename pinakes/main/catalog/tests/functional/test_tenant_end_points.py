"""Module to test Tenant end points"""
import json
import pytest
from pinakes.main.tests.factories import TenantFactory


@pytest.mark.django_db
def test_tenant_list(api_request):
    """Get a list of tenant objects"""
    TenantFactory()
    response = api_request("get", "catalog:tenant-list")

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 2  # including the default


@pytest.mark.django_db
def test_tenant_retrieve(api_request):
    """Retrieve a tenant based on its id"""
    tenant = TenantFactory()
    response = api_request("get", "catalog:tenant-detail", tenant.id)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == tenant.id


@pytest.mark.django_db
def test_tenant_delete_fail(api_request):
    """Delete on Tenant not supported"""
    tenant = TenantFactory()
    response = api_request("delete", "catalog:tenant-detail", tenant.id)

    assert response.status_code == 405


@pytest.mark.django_db
def test_tenant_patch_fail(api_request):
    """Patch on Tenant not supported"""
    tenant = TenantFactory()
    data = {"external_tenant": "abcdef"}
    response = api_request("put", "catalog:tenant-detail", tenant.id, data)

    assert response.status_code == 405


@pytest.mark.django_db
def test_tenant_post_fail(api_request):
    """Post on Tenant not supported"""
    TenantFactory()
    data = {"external_tenant": "abcdef"}
    response = api_request("post", "catalog:tenant-list", data=data)

    assert response.status_code == 405
