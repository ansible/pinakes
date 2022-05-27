"""Module for testing Approval Templates"""
import json
import pytest
from pinakes.main.approval.tests.factories import (
    NotificationSettingFactory,
    TemplateFactory,
    WorkflowFactory,
)
from pinakes.main.approval.permissions import (
    TemplatePermission,
    WorkflowPermission,
)


@pytest.mark.django_db
def test_template_list(api_request, mocker):
    """Get a list of templates"""
    has_permission = mocker.spy(TemplatePermission, "has_permission")
    TemplateFactory()
    response = api_request("get", "approval:template-list")

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["count"] == 2  # including the default
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_template_retrieve(api_request, mocker):
    """RETRIEVE a template by its id"""
    has_permission = mocker.spy(TemplatePermission, "has_permission")
    template = TemplateFactory()
    response = api_request("get", "approval:template-detail", template.id)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == template.id
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_template_delete(api_request, mocker):
    """Delete a template"""
    has_permission = mocker.spy(TemplatePermission, "has_permission")
    template = TemplateFactory()
    response = api_request("delete", "approval:template-detail", template.id)

    assert response.status_code == 204
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_template_patch(api_request, mocker):
    """Update a template"""
    has_permission = mocker.spy(TemplatePermission, "has_permission")
    template = TemplateFactory()
    response = api_request(
        "patch", "approval:template-detail", template.id, {"title": "update"}
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["title"] == "update"
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_template_put_not_supported(api_request):
    """PUT on a template should fail"""
    template = TemplateFactory()
    response = api_request(
        "put", "approval:template-detail", template.id, {"title": "update"}
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_template_workflows_get(api_request, mocker):
    """Fetch workflows for a template"""
    has_permission = mocker.spy(WorkflowPermission, "has_permission")
    template = TemplateFactory()
    workflow = WorkflowFactory(template=template)
    response = api_request(
        "get", "approval:template-workflow-list", template.id
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1
    assert content["results"][0]["id"] == workflow.id
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_template_post(api_request, mocker):
    """Create a template"""
    has_permission = mocker.spy(TemplatePermission, "has_permission")
    notification1 = NotificationSettingFactory()
    notification2 = NotificationSettingFactory()
    data = {
        "title": "abcdef",
        "description": "abc",
        "process_method": notification1.id,
        "signal_method": notification2.id,
    }

    response = api_request("post", "approval:template-list", data=data)

    assert response.status_code == 201
    content = response.data
    assert content["title"] == "abcdef"
    assert content["description"] == "abc"
    assert content["process_method"] == notification1.id
    assert content["signal_method"] == notification2.id
    has_permission.assert_called_once()

    response = api_request("post", "approval:template-list", data=data)
    # uniqueness
    assert response.status_code == 400
