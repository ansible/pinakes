""" Module to test approval workflows """
import json
import pytest
from django.urls import reverse
from approval.tests.factories import TemplateFactory
from approval.tests.factories import WorkflowFactory


@pytest.mark.django_db
def test_workflow_list(api_request):
    """GET a list of workflows"""
    WorkflowFactory()
    url = reverse("approval:workflow-list")
    response = api_request("get", url)

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1


@pytest.mark.django_db
def test_workflow_retrieve(api_request):
    """Retrieve a workflow by its ID"""
    workflow = WorkflowFactory()
    url = reverse("approval:workflow-detail", args=(workflow.id,))
    response = api_request("get", url)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == workflow.id


@pytest.mark.django_db
def test_workflow_delete(api_request):
    """Delete a Workflow by its ID"""
    workflow = WorkflowFactory()
    url = reverse("approval:workflow-detail", args=(workflow.id,))
    response = api_request("delete", url)

    assert response.status_code == 204


@pytest.mark.django_db
def test_workflow_patch(api_request):
    """PATCH a Workflow by its ID"""
    workflow = WorkflowFactory()
    url = reverse("approval:workflow-detail", args=(workflow.id,))
    response = api_request("patch", url, {"name": "update"})

    assert response.status_code == 200


@pytest.mark.django_db
def test_workflow_put_not_supported(api_request):
    """PUT not supported on Workflow"""
    workflow = WorkflowFactory()
    url = reverse("approval:workflow-detail", args=(workflow.id,))
    response = api_request("put", url, {"name": "update"})

    assert response.status_code == 405


@pytest.mark.django_db
def test_workflow_post(api_request):
    """Create a new Workflow"""
    template = TemplateFactory()
    url = reverse("approval:workflow-list")
    response = api_request(
        "post",
        url,
        {
            "template": template.id,
            "name": "abcdef",
            "description": "abc",
        },
    )

    assert response.status_code == 201
