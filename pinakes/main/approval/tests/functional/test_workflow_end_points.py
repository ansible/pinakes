""" Module to test approval workflows """
import json
import pytest
from pinakes.main.approval.tests.factories import (
    TemplateFactory,
)
from pinakes.main.approval.tests.factories import (
    WorkflowFactory,
)
from pinakes.main.catalog.tests.factories import (
    PortfolioFactory,
)
from pinakes.main.approval.tests.services.test_link_workflow import (
    create_and_link,
)


@pytest.mark.django_db
def test_workflow_list(api_request):
    """GET a list of workflows"""
    WorkflowFactory()
    response = api_request("get", "approval:workflow-list")

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1


@pytest.mark.django_db
def test_searching(api_request):
    """Search by query parameter"""
    WorkflowFactory(name="alpha", description="hello")
    WorkflowFactory(name="beta", description="world")
    response = api_request(
        "get", "approval:workflow-list", data={"search": "eta"}
    )
    content = json.loads(response.content)
    assert content["count"] == 1
    assert content["results"][0]["name"] == "beta"

    response = api_request(
        "get", "approval:workflow-list", data={"search": "l"}
    )
    content = json.loads(response.content)
    assert content["count"] == 2

    response = api_request(
        "get", "approval:workflow-list", data={"search": "xyz"}
    )
    content = json.loads(response.content)
    assert content["count"] == 0


@pytest.mark.django_db
def test_filtering(api_request):
    """Filter by query parameter"""
    WorkflowFactory(name="alpha", description="hello")
    WorkflowFactory(name="beta", description="world")
    response = api_request(
        "get",
        "approval:workflow-list",
        data={"name": "beta", "description": "world"},
    )
    content = json.loads(response.content)
    assert content["count"] == 1
    assert content["results"][0]["name"] == "beta"

    response = api_request(
        "get", "approval:workflow-list", data={"name": "bet"}
    )
    content = json.loads(response.content)
    assert content["count"] == 0


@pytest.mark.django_db
def test_ordering(api_request):
    """Filter by query parameter"""
    WorkflowFactory(name="alpha", description="hello")
    WorkflowFactory(name="beta", description="world")
    response = api_request("get", "approval:workflow-list")
    content = json.loads(response.content)
    assert content["results"][0]["name"] == "alpha"
    assert content["results"][1]["name"] == "beta"

    response = api_request(
        "get", "approval:workflow-list", data={"ordering": "name"}
    )
    content = json.loads(response.content)
    assert content["results"][0]["name"] == "alpha"
    assert content["results"][1]["name"] == "beta"

    response = api_request(
        "get", "approval:workflow-list", data={"ordering": "-name"}
    )
    content = json.loads(response.content)
    assert content["results"][0]["name"] == "beta"
    assert content["results"][1]["name"] == "alpha"


@pytest.mark.django_db
def test_list_by_external_object(api_request):
    """List workflows by linked external object"""
    _workflow, _portfolio, resource_obj = create_and_link()

    response = api_request("get", "approval:workflow-list", data=resource_obj)
    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["count"] == 1


@pytest.mark.django_db
def test_workflow_link_bad(api_request):
    resource_obj = {"object_id": 1}

    response = api_request("get", "approval:workflow-list", data=resource_obj)

    assert response.status_code == 400


@pytest.mark.django_db
def test_workflow_retrieve(api_request):
    """Retrieve a workflow by its ID"""
    workflow = WorkflowFactory()
    response = api_request("get", "approval:workflow-detail", workflow.id)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == workflow.id


@pytest.mark.django_db
def test_workflow_delete(api_request):
    """Delete a Workflow by its ID"""
    workflow = WorkflowFactory()
    response = api_request("delete", "approval:workflow-detail", workflow.id)

    assert response.status_code == 204


@pytest.mark.django_db
def test_workflow_patch(api_request, mocker):
    """PATCH a Workflow by its ID"""
    workflow = WorkflowFactory()
    group_refs = [{"name": "group1", "uuid": "uuid1"}]
    args = (
        "patch",
        "approval:workflow-detail",
        workflow.id,
        {"name": "update", "group_refs": group_refs},
    )

    assert api_request(*args).status_code == 400

    mocker.patch(
        "pinakes.main.approval.validations.validate_approver_groups",
        return_value=group_refs,
    )
    response = api_request(*args)
    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["name"] == "update"
    assert content["group_refs"] == group_refs


@pytest.mark.django_db
def test_workflow_put_not_supported(api_request):
    """PUT not supported on Workflow"""
    workflow = WorkflowFactory()
    response = api_request(
        "put", "approval:workflow-detail", workflow.id, {"name": "update"}
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_workflow_post(api_request, mocker):
    """Create a new Workflow"""
    template = TemplateFactory()
    group_refs = [{"name": "group1", "uuid": "uuid1"}]
    args = (
        "post",
        "approval:template-workflow-list",
        template.id,
        {
            "name": "abcdef",
            "description": "abc",
            "group_refs": group_refs,
        },
    )

    assert api_request(*args).status_code == 400

    mocker.patch(
        "pinakes.main.approval.validations.validate_approver_groups",
        return_value=group_refs,
    )
    assert api_request(*args).status_code == 201


@pytest.mark.django_db
def test_workflow_post_bad(api_request):
    """Create a new Workflow but lack group uuid"""
    template = TemplateFactory()
    response = api_request(
        "post",
        "approval:template-workflow-list",
        template.id,
        {
            "name": "abcdef",
            "description": "abc",
            "group_refs": [{"name": "group1"}],
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

    response = api_request(
        "post", "approval:workflow-link", workflow.id, resource_obj
    )

    assert response.status_code == 204


@pytest.mark.django_db
def test_workflow_unlink(api_request):
    """Remove approval tag on a remote object"""
    workflow, _portfolio, resource_obj = create_and_link()

    response = api_request(
        "post", "approval:workflow-unlink", workflow.id, resource_obj
    )

    assert response.status_code == 204
