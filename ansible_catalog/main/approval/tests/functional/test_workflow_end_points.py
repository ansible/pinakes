""" Module to test approval workflows """
import json
import pytest
from ansible_catalog.main.approval.tests.factories import TemplateFactory
from ansible_catalog.main.approval.tests.factories import WorkflowFactory
from ansible_catalog.main.catalog.tests.factories import PortfolioFactory
from ansible_catalog.main.approval.tests.services.test_link_workflow import (
    create_and_link,
)


@pytest.mark.django_db
def test_workflow_list(api_request):
    """GET a list of workflows"""
    WorkflowFactory()
    response = api_request("get", "workflow-list")

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1


@pytest.mark.django_db
def test_searching(api_request):
    """Search by query parameter"""
    WorkflowFactory(name="alpha", description="hello")
    WorkflowFactory(name="beta", description="world")
    response = api_request("get", "workflow-list", data={"search": "eta"})
    content = json.loads(response.content)
    assert content["count"] == 1
    assert content["results"][0]["name"] == "beta"

    response = api_request("get", "workflow-list", data={"search": "l"})
    content = json.loads(response.content)
    assert content["count"] == 2

    response = api_request("get", "workflow-list", data={"search": "xyz"})
    content = json.loads(response.content)
    assert content["count"] == 0


@pytest.mark.django_db
def test_filtering(api_request):
    """Filter by query parameter"""
    WorkflowFactory(name="alpha", description="hello")
    WorkflowFactory(name="beta", description="world")
    response = api_request(
        "get", "workflow-list", data={"name": "beta", "description": "world"}
    )
    content = json.loads(response.content)
    assert content["count"] == 1
    assert content["results"][0]["name"] == "beta"

    response = api_request("get", "workflow-list", data={"name": "bet"})
    content = json.loads(response.content)
    assert content["count"] == 0


@pytest.mark.django_db
def test_ordering(api_request):
    """Filter by query parameter"""
    WorkflowFactory(name="alpha", description="hello")
    WorkflowFactory(name="beta", description="world")
    response = api_request("get", "workflow-list")
    content = json.loads(response.content)
    assert content["results"][0]["name"] == "alpha"
    assert content["results"][1]["name"] == "beta"

    response = api_request("get", "workflow-list", data={"ordering": "name"})
    content = json.loads(response.content)
    assert content["results"][0]["name"] == "alpha"
    assert content["results"][1]["name"] == "beta"

    response = api_request("get", "workflow-list", data={"ordering": "-name"})
    content = json.loads(response.content)
    assert content["results"][0]["name"] == "beta"
    assert content["results"][1]["name"] == "alpha"


@pytest.mark.django_db
def test_list_by_external_object(api_request):
    """List workflows by linked external object"""
    _workflow, _portfolio, resource_obj = create_and_link()

    response = api_request("get", "workflow-list", data=resource_obj)
    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["count"] == 1


@pytest.mark.django_db
def test_workflow_link_bad(api_request):
    resource_obj = {"object_id": 1}

    response = api_request("get", "workflow-list", data=resource_obj)

    assert response.status_code == 400


@pytest.mark.django_db
def test_workflow_retrieve(api_request):
    """Retrieve a workflow by its ID"""
    workflow = WorkflowFactory()
    response = api_request("get", "workflow-detail", workflow.id)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == workflow.id


@pytest.mark.django_db
def test_workflow_delete(api_request):
    """Delete a Workflow by its ID"""
    workflow = WorkflowFactory()
    response = api_request("delete", "workflow-detail", workflow.id)

    assert response.status_code == 204


@pytest.mark.django_db
def test_workflow_patch(api_request):
    """PATCH a Workflow by its ID"""
    workflow = WorkflowFactory()
    response = api_request(
        "patch", "workflow-detail", workflow.id, {"name": "update"}
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_workflow_put_not_supported(api_request):
    """PUT not supported on Workflow"""
    workflow = WorkflowFactory()
    response = api_request(
        "put", "workflow-detail", workflow.id, {"name": "update"}
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_workflow_post(api_request):
    """Create a new Workflow"""
    template = TemplateFactory()
    response = api_request(
        "post",
        "template-workflow-list",
        template.id,
        {
            "name": "abcdef",
            "description": "abc",
            "group_refs": [{"name": "group1", "uuid": "uuid1"}]
        },
    )

    assert response.status_code == 201


@pytest.mark.django_db
def test_workflow_post_bad(api_request):
    """Create a new Workflow but lack group uuid"""
    template = TemplateFactory()
    response = api_request(
        "post",
        "template-workflow-list",
        template.id,
        {
            "name": "abcdef",
            "description": "abc",
            "group_refs": [{"name": "group1"}]
        },
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_workflow_link(api_request):
    workflow = WorkflowFactory()
    portfolio = PortfolioFactory()
    resource_obj = {
        "object_type": "Portfolio",
        "object_id": portfolio.id,
        "app_name": "catalog",
    }

    response = api_request("post", "workflow-link", workflow.id, resource_obj)

    assert response.status_code == 204


@pytest.mark.django_db
def test_workflow_unlink(api_request):
    """Remove approval tag on a remote object"""
    workflow, _portfolio, resource_obj = create_and_link()

    response = api_request(
        "post", "workflow-unlink", workflow.id, resource_obj
    )

    assert response.status_code == 204
