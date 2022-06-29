"""Module to test approval workflows"""
import json
import pytest
from pinakes.main.approval.tests.factories import (
    TemplateFactory,
    WorkflowFactory,
    RequestFactory,
)
from pinakes.main.catalog.tests.factories import (
    PortfolioFactory,
)
from pinakes.main.approval.tests.services.test_link_workflow import (
    create_and_link,
)
from pinakes.main.approval.permissions import WorkflowPermission


@pytest.mark.django_db
def test_workflow_list(api_request, mocker):
    """GET a list of workflows"""
    has_permission = mocker.spy(WorkflowPermission, "has_permission")
    WorkflowFactory()
    response = api_request("get", "approval:workflow-list")

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_searching(api_request, mocker):
    """Search by query parameter"""
    has_permission = mocker.spy(WorkflowPermission, "has_permission")
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
    assert has_permission.call_count == 3


@pytest.mark.django_db
def test_filtering(api_request, mocker):
    """Filter by query parameter"""
    has_permission = mocker.spy(WorkflowPermission, "has_permission")
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
    assert has_permission.call_count == 2


@pytest.mark.django_db
def test_ordering(api_request, mocker):
    """Filter by query parameter"""
    has_permission = mocker.spy(WorkflowPermission, "has_permission")
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
    assert has_permission.call_count == 3


@pytest.mark.django_db
def test_pagination(api_request, mocker):
    """Accept query parameter for pagination"""
    WorkflowFactory(name="alpha", description="hello")
    WorkflowFactory(name="beta", description="world")
    WorkflowFactory(name="gamma", description="!")

    response = api_request(
        "get", "approval:workflow-list", data={"page": 2, "page_size": 2}
    )
    assert response.data["count"] == 3
    assert len(response.data["results"]) == 1
    assert response.data["next"] is None
    assert response.data["previous"] is not None


@pytest.mark.django_db
def test_list_by_external_object(api_request):
    """List workflows by linked external object"""
    _workflow, _portfolio, resource_obj = create_and_link()

    response = api_request("get", "approval:workflow-list", data=resource_obj)
    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["count"] == 1


@pytest.mark.django_db
def test_workflow_link_bad(api_request, mocker):
    """Linking a workflow fails when resource_obj parameters are incomplete"""
    has_permission = mocker.spy(WorkflowPermission, "has_permission")
    resource_obj = {"object_id": 1}

    response = api_request("get", "approval:workflow-list", data=resource_obj)

    assert response.status_code == 400
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_workflow_retrieve(api_request, mocker):
    """Retrieve a workflow by its ID"""
    has_permission = mocker.spy(WorkflowPermission, "has_permission")
    workflow = WorkflowFactory()
    response = api_request("get", "approval:workflow-detail", workflow.id)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == workflow.id
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_workflow_delete(api_request, mocker):
    """Delete a Workflow by its ID"""
    has_permission = mocker.spy(WorkflowPermission, "has_permission")
    workflow = WorkflowFactory()
    response = api_request("delete", "approval:workflow-detail", workflow.id)

    assert response.status_code == 204
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_workflow_delete_forbbiden(api_request, mocker):
    """Delete a Workflow by its ID"""
    has_permission = mocker.spy(WorkflowPermission, "has_permission")
    workflow = WorkflowFactory()
    RequestFactory(state="pending", workflow=workflow)
    response = api_request("delete", "approval:workflow-detail", workflow.id)

    assert response.status_code == 400
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_workflow_patch(api_request, mocker):
    """PATCH a Workflow by its ID"""
    has_permission = mocker.spy(WorkflowPermission, "has_permission")
    workflow = WorkflowFactory()
    template = TemplateFactory()
    group_refs = [{"name": "group1", "uuid": "uuid1"}]
    args = (
        "patch",
        "approval:workflow-detail",
        workflow.id,
        {"name": "update", "group_refs": group_refs, "template": template.id},
    )

    assert api_request(*args).status_code == 400

    mocker.patch(
        "pinakes.main.approval.validations.validate_approver_groups",
        return_value=group_refs,
    )
    response = api_request(*args)
    assert response.status_code == 200
    content = response.data
    assert content["name"] == "update"
    assert content["group_refs"] == group_refs
    assert content["template"] == template.id
    assert has_permission.call_count == 2


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
    has_permission = mocker.spy(WorkflowPermission, "has_permission")
    template = TemplateFactory()
    group_refs = [{"name": "group1", "uuid": "uuid1"}]
    data = {
        "name": "abcdef",
        "description": "abc",
        "group_refs": group_refs,
        "template": template.id,
    }

    response = api_request("post", "approval:workflow-list", data=data)
    assert response.status_code == 400

    mocker.patch(
        "pinakes.main.approval.validations.validate_approver_groups",
        return_value=group_refs,
    )
    response = api_request("post", "approval:workflow-list", data=data)
    assert response.status_code == 201
    assert has_permission.call_count == 2


@pytest.mark.django_db
def test_workflow_post_bad(api_request, mocker):
    """Create a new Workflow but lack group uuid"""
    has_permission = mocker.spy(WorkflowPermission, "has_permission")
    template = TemplateFactory()
    response = api_request(
        "post",
        "approval:workflow-list",
        data={
            "name": "abcdef",
            "description": "abc",
            "group_refs": [{"name": "group1"}],
            "template": template.id,
        },
    )

    assert response.status_code == 400
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_workflow_link(api_request, mocker):
    """Add an approval tag to a resource object"""
    has_permission = mocker.spy(WorkflowPermission, "has_permission")
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
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_workflow_unlink(api_request, mocker):
    """Remove approval tag on a remote object"""
    has_permission = mocker.spy(WorkflowPermission, "has_permission")
    workflow, _portfolio, resource_obj = create_and_link()

    response = api_request(
        "post", "approval:workflow-unlink", workflow.id, resource_obj
    )

    assert response.status_code == 204
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_workflow_relative_reposition(api_request, mocker):
    """Adjust workflow sequence by increment"""
    has_permission = mocker.spy(WorkflowPermission, "has_permission")
    workflow = WorkflowFactory()

    data = {"increment": -1}
    response = api_request(
        "post", "approval:workflow-reposition", workflow.id, data
    )
    assert response.status_code == 204
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_workflow_absolute_reposition(api_request, mocker):
    """Adjust workflow sequence by placement"""
    has_permission = mocker.spy(WorkflowPermission, "has_permission")
    workflow = WorkflowFactory()

    data = {"placement": "top"}
    response = api_request(
        "post", "approval:workflow-reposition", workflow.id, data
    )

    assert response.status_code == 204
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_workflow_reposition_both(api_request, mocker):
    """Adjust workflow sequence by increment"""
    has_permission = mocker.spy(WorkflowPermission, "has_permission")
    workflow = WorkflowFactory()

    data = {"increment": -1, "placement": "top"}
    response = api_request(
        "post", "approval:workflow-reposition", workflow.id, data
    )
    assert response.status_code == 400
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_workflow_reposition_none(api_request, mocker):
    """Adjust workflow sequence by placement"""
    has_permission = mocker.spy(WorkflowPermission, "has_permission")
    workflow = WorkflowFactory()

    data = {"something": "else"}
    response = api_request(
        "post", "approval:workflow-reposition", workflow.id, data
    )

    assert response.status_code == 400
    has_permission.assert_called_once()
