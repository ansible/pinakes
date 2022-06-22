"""Module to test approval requests and actions"""
import json
import pytest
from pinakes.main.tests.factories import default_tenant
from pinakes.main.approval.tests.factories import (
    RequestFactory,
    RequestContextFactory,
    ActionFactory,
)
from pinakes.main.approval.services.send_event import (
    SendEvent,
)
from pinakes.main.approval.permissions import (
    RequestPermission,
    ActionPermission,
)


@pytest.mark.django_db
def test_request_list(api_request, mocker):
    scope_queryset = mocker.spy(RequestPermission, "scope_queryset")
    RequestFactory()
    RequestFactory()
    response = api_request(
        "get", "approval:request-list", data={"persona": "admin"}
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 2
    scope_queryset.assert_called_once()


@pytest.mark.django_db
def test_request_retrieve(api_request, mocker):
    obj_permission = mocker.spy(RequestPermission, "has_object_permission")
    request = RequestFactory(group_name="group1")
    response = api_request("get", "approval:request-detail", request.id)

    assert response.status_code == 200
    assert response.data["id"] == request.id
    assert response.data["group_name"] == request.group_name
    obj_permission.assert_called_once()


@pytest.mark.django_db
def test_request_content_retrieve(api_request):
    """Test get request content"""
    request_context = RequestContextFactory(content={"param1": "val1"})
    request = RequestFactory(request_context=request_context)
    response = api_request("get", "approval:request-content", request.id)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["param1"] == "val1"


@pytest.mark.django_db
def test_request_child_list(api_request):
    parent = RequestFactory()
    RequestFactory(parent=parent)
    RequestFactory(parent=parent)
    response = api_request(
        "get",
        "approval:request-request-list",
        parent.id,
        data={"persona": "admin"},
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 2


@pytest.mark.django_db
def test_request_action_list(api_request, mocker):
    has_permission = mocker.spy(ActionPermission, "has_permission")
    request = RequestFactory()
    ActionFactory(request=request, operation="start")
    ActionFactory(request=request, operation="complete")
    response = api_request("get", "approval:request-action-list", request.id)

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 2
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_create_request_not_support(api_request):
    default_tenant()
    response = api_request(
        "post",
        "approval:request-list",
        data={
            "name": "abcdef",
            "description": "abc",
            "content": {"item1": "val1"},
            "tag_resources": [
                {
                    "app_name": "catalog",
                    "object_type": "portfolio",
                    "tags": ["tag1", "tag2"],
                }
            ],
        },
    )
    assert response.status_code == 405


@pytest.mark.django_db
def test_create_action(api_request, mocker):
    has_permission = mocker.spy(ActionPermission, "has_permission")
    mocker.patch.object(SendEvent, "process")
    request = RequestFactory(state="notified")
    response = api_request(
        "post",
        "approval:request-action-list",
        request.id,
        {
            "operation": "deny",
            "comments": "not good",
        },
    )
    assert response.status_code == 201
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_create_action_no_comments(api_request, mocker):
    has_permission = mocker.spy(ActionPermission, "has_permission")
    mocker.patch.object(SendEvent, "process")
    request = RequestFactory(state="notified")
    response = api_request(
        "post",
        "approval:request-action-list",
        request.id,
        {
            "operation": "approve",
        },
    )
    assert response.status_code == 201
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_retrieve_action(api_request, mocker):
    has_permission = mocker.spy(ActionPermission, "has_object_permission")
    request = RequestFactory()
    action = ActionFactory(request=request)
    response = api_request(
        "get",
        "approval:action-detail",
        action.id,
    )
    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == action.id
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_request_not_supported_methods(api_request):
    request = RequestFactory()

    response = api_request(
        "put", "approval:request-detail", request.id, {"name": "update"}
    )
    assert response.status_code == 405

    response = api_request(
        "patch", "approval:request-detail", request.id, {"name": "update"}
    )
    assert response.status_code == 405

    response = api_request(
        "delete",
        "approval:request-detail",
        request.id,
    )
    assert response.status_code == 405


@pytest.mark.django_db
def test_request_request_not_create(api_request):
    request = RequestFactory()
    response = api_request(
        "post",
        "approval:request-request-list",
        request.id,
        {
            "name": "child",
            "description": "child request cannot be explicitly created",
            "parent": request.id,
        },
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_request_extra_data(api_request):
    parent = RequestFactory()
    child = RequestFactory(parent=parent)
    parent_action = ActionFactory(request=parent)
    child_action = ActionFactory(request=child)

    response = api_request(
        "get", "approval:request-detail", parent.id, data={"extra": "true"}
    )
    content = json.loads(response.content)
    assert response.status_code == 200
    assert content["extra_data"]["subrequests"][0]["name"] == child.name
    assert content["extra_data"]["subrequests"][0]["id"] == child.id
    assert (
        content["extra_data"]["actions"][0]["operation"]
        == parent_action.operation
    )
    assert content["extra_data"]["actions"][0]["id"] == parent_action.id
    assert (
        content["extra_data"]["subrequests"][0]["actions"][0]["operation"]
        == child_action.operation
    )
    assert (
        content["extra_data"]["subrequests"][0]["actions"][0]["id"]
        == child_action.id
    )
