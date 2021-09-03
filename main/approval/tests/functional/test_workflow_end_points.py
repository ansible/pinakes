""" Module to test approval workflows """
import json
import pytest
from django.urls import reverse
from main.approval.tests.factories import TemplateFactory
from main.approval.tests.factories import WorkflowFactory


@pytest.mark.django_db
def test_workflow_list(api_request):
    """GET a list of workflows"""
    WorkflowFactory()
    url = reverse("workflow-list")
    response = api_request("get", url)

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1


@pytest.mark.django_db
def test_searching(api_request):
    """Search by query parameter"""
    WorkflowFactory(name="alpha", description="hello")
    WorkflowFactory(name="beta", description="world")
    url = reverse("workflow-list")
    response = api_request("get", url, {"search": "eta"})
    content = json.loads(response.content)
    assert content["count"] == 1
    assert content["results"][0]["name"] == "beta"

    response = api_request("get", url, {"search": "l"})
    content = json.loads(response.content)
    assert content["count"] == 2

    response = api_request("get", url, {"search": "xyz"})
    content = json.loads(response.content)
    assert content["count"] == 0


@pytest.mark.django_db
def test_filtering(api_request):
    """Filter by query parameter"""
    WorkflowFactory(name="alpha", description="hello")
    WorkflowFactory(name="beta", description="world")
    url = reverse("workflow-list")
    response = api_request(
        "get", url, {"name": "beta", "description": "world"}
    )
    content = json.loads(response.content)
    assert content["count"] == 1
    assert content["results"][0]["name"] == "beta"

    response = api_request("get", url, {"name": "bet"})
    content = json.loads(response.content)
    assert content["count"] == 0


@pytest.mark.django_db
def test_ordering(api_request):
    """Filter by query parameter"""
    WorkflowFactory(name="alpha", description="hello")
    WorkflowFactory(name="beta", description="world")
    url = reverse("workflow-list")
    response = api_request("get", url)
    content = json.loads(response.content)
    assert content["results"][0]["name"] == "alpha"
    assert content["results"][1]["name"] == "beta"

    response = api_request("get", url, {"ordering": "name"})
    content = json.loads(response.content)
    assert content["results"][0]["name"] == "alpha"
    assert content["results"][1]["name"] == "beta"

    response = api_request("get", url, {"ordering": "-name"})
    content = json.loads(response.content)
    assert content["results"][0]["name"] == "beta"
    assert content["results"][1]["name"] == "alpha"


@pytest.mark.django_db
def test_workflow_retrieve(api_request):
    """Retrieve a workflow by its ID"""
    workflow = WorkflowFactory()
    url = reverse("workflow-detail", args=(workflow.id,))
    response = api_request("get", url)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == workflow.id


@pytest.mark.django_db
def test_workflow_delete(api_request):
    """Delete a Workflow by its ID"""
    workflow = WorkflowFactory()
    url = reverse("workflow-detail", args=(workflow.id,))
    response = api_request("delete", url)

    assert response.status_code == 204


@pytest.mark.django_db
def test_workflow_patch(api_request):
    """PATCH a Workflow by its ID"""
    workflow = WorkflowFactory()
    url = reverse("workflow-detail", args=(workflow.id,))
    response = api_request("patch", url, {"name": "update"})

    assert response.status_code == 200


@pytest.mark.django_db
def test_workflow_put_not_supported(api_request):
    """PUT not supported on Workflow"""
    workflow = WorkflowFactory()
    url = reverse("workflow-detail", args=(workflow.id,))
    response = api_request("put", url, {"name": "update"})

    assert response.status_code == 405


@pytest.mark.django_db
def test_workflow_post(api_request):
    """Create a new Workflow"""
    template = TemplateFactory()
    url = reverse("template-workflow-list", args=(template.id,))
    response = api_request(
        "post",
        url,
        {
            "name": "abcdef",
            "description": "abc",
        },
    )

    assert response.status_code == 201
