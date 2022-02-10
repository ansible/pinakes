""" Module for testing Approval Templates """
import json
import pytest
from automation_services_catalog.main.tests.factories import TenantFactory
from automation_services_catalog.main.approval.tests.factories import (
    TemplateFactory,
    WorkflowFactory,
)


@pytest.mark.django_db
def test_template_list(api_request):
    """Get a list of templates"""
    TemplateFactory()
    response = api_request("get", "approval:template-list")

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["count"] == 2  # including the default


@pytest.mark.django_db
def test_template_retrieve(api_request):
    """RETRIEVE a template by its id"""
    template = TemplateFactory()
    response = api_request("get", "approval:template-detail", template.id)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == template.id


@pytest.mark.django_db
def test_template_delete(api_request):
    template = TemplateFactory()
    response = api_request("delete", "approval:template-detail", template.id)

    assert response.status_code == 204


@pytest.mark.django_db
def test_template_patch(api_request):
    template = TemplateFactory()
    response = api_request(
        "patch", "approval:template-detail", template.id, {"title": "update"}
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["title"] == "update"


@pytest.mark.django_db
def test_portfolio_put_not_supported(api_request):
    """PUT on a template should fail"""
    template = TemplateFactory()
    response = api_request(
        "put", "approval:template-detail", template.id, {"title": "update"}
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_template_workflows_get(api_request):
    """Fetch workflows for a template"""
    template = TemplateFactory()
    workflow = WorkflowFactory(template=template)
    response = api_request(
        "get", "approval:template-workflow-list", template.id
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1
    assert content["results"][0]["id"] == workflow.id


@pytest.mark.django_db
def test_template_post(api_request):
    TenantFactory()
    response = api_request(
        "post",
        "approval:template-list",
        data={"title": "abcdef", "description": "abc"},
    )

    assert response.status_code == 201
    content = json.loads(response.content)
    assert content["title"] == "abcdef"
    assert content["description"] == "abc"
