""" Module to test approval requests and actions """
import json
import pytest
from automation_services_catalog.main.tests.factories import default_tenant
from automation_services_catalog.main.approval.tests.factories import (
    RequestFactory,
    RequestContextFactory,
    ActionFactory,
)
from automation_services_catalog.main.approval.services.send_event import (
    SendEvent,
)


@pytest.mark.django_db
def test_request_list(api_request):
    RequestFactory()
    RequestFactory()
    response = api_request("get", "approval:request-list")

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 2


@pytest.mark.django_db
def test_request_retrieve(api_request):
    request = RequestFactory()
    response = api_request("get", "approval:request-detail", request.id)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == request.id


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
    response = api_request("get", "approval:request-request-list", parent.id)

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 2


@pytest.mark.django_db
def test_request_action_list(api_request):
    request = RequestFactory()
    ActionFactory(request=request, operation="start")
    ActionFactory(request=request, operation="complete")
    response = api_request("get", "approval:request-action-list", request.id)

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 2


@pytest.mark.django_db
def test_create_request(api_request, mocker):
    mocker.patch("django_rq.enqueue")
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
    assert response.status_code == 201
    content = json.loads(response.content)
    assert content["state"] == "pending"


@pytest.mark.django_db
def test_create_request_user_error(api_request):
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
                    "obj_type": "portfolio",
                    "tags": ["tag1", "tag2"],
                }
            ],
        },
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_request_internal_error(api_request, mocker):
    mocker.patch("django_rq.enqueue", side_effect=Exception("whoops"))
    default_tenant()
    response = api_request(
        "post",
        "approval:request-list",
        data={
            "name": "abcdef",
            "description": "abc",
            "content": {"item1": "val1"},
        },
    )

    assert response.status_code == 500
    content = json.loads(response.content)
    assert content["detail"] == "Internal Error"


@pytest.mark.django_db
def test_create_action(api_request, mocker):
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
