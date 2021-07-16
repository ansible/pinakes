""" Module to test approval requests and actions """
import pytest
import json
from django.urls import reverse
from approval.tests.factories import (
    RequestFactory,
    ActionFactory,
    default_tenant,
)


@pytest.mark.django_db
def test_request_list(api_request):
    RequestFactory()
    RequestFactory()
    url = reverse("approval:request-list")
    response = api_request("get", url)

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 2


@pytest.mark.django_db
def test_request_retrieve(api_request):
    request = RequestFactory()
    url = reverse("approval:request-detail", args=(request.id,))
    response = api_request("get", url)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == request.id


@pytest.mark.django_db
def test_request_child_list(api_request):
    parent = RequestFactory()
    RequestFactory(parent=parent)
    RequestFactory(parent=parent)
    url = reverse("approval:request-request-list", args=(parent.id,))
    response = api_request("get", url)

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 2


@pytest.mark.django_db
def test_request_child_detail(api_request):
    parent = RequestFactory()
    child = RequestFactory(parent=parent)
    url = reverse("approval:request-request-detail", args=(parent.id, child.id))
    response = api_request("get", url)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == child.id


@pytest.mark.django_db
def test_request_action_list(api_request):
    request = RequestFactory()
    ActionFactory(request=request, operation="Start")
    ActionFactory(request=request, operation="Complete")
    url = reverse("approval:request-action-list", args=(request.id,))
    response = api_request("get", url)

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 2


@pytest.mark.django_db
def test_request_action_detail(api_request):
    request = RequestFactory()
    action = ActionFactory(request=request)
    url = reverse("approval:request-action-detail", args=(request.id, action.id))
    response = api_request("get", url)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == action.id


@pytest.mark.django_db
def test_create_request(api_request):
    default_tenant()
    url = reverse("approval:request-list")
    response = api_request(
        "post",
        url,
        {
            "name": "abcdef",
            "description": "abc",
            "content": {"item1": "val1"}
        },
    )

    assert response.status_code == 201
    content = json.loads(response.content)
    assert content["state"] == "Pending"


@pytest.mark.django_db
def test_create_action(api_request):
    request = RequestFactory()
    url = reverse("approval:request-action-list", args=(request.id,))
    response = api_request(
        "post",
        url,
        {
            "operation": "Deny",
            "comments": "not good",
            "request": request.id,
        },
    )

    assert response.status_code == 201


@pytest.mark.django_db
def test_request_not_supported_methods(api_request):
    request = RequestFactory()
    url = reverse("approval:request-detail", args=(request.id,))

    response = api_request("put", url, {"name": "update"})
    assert response.status_code == 405

    response = api_request("patch", url, {"name": "update"})
    assert response.status_code == 405

    response = api_request("delete", url)
    assert response.status_code == 405


@pytest.mark.django_db
def test_request_request_not_create(api_request):
    request = RequestFactory()
    url = reverse("approval:request-request-list", args=(request.id,))
    response = api_request(
        "post",
        url,
        {
            "name": "child",
            "description": "child request cannot be explictly created",
            "parent": request.id,
        },
    )

    assert response.status_code == 400       


@pytest.mark.django_db
def test_request_request_not_supported_methods(api_request):
    parent = RequestFactory()
    child = RequestFactory(parent=parent)
    url = reverse("approval:request-request-detail", args=(parent.id,child.id,))

    response = api_request("put", url, {"name": "update"})
    assert response.status_code == 405

    response = api_request("patch", url, {"name": "update"})
    assert response.status_code == 405

    response = api_request("delete", url)
    assert response.status_code == 405


@pytest.mark.django_db
def test_request_action_not_supported_methods(api_request):
    request = RequestFactory()
    action = ActionFactory(request=request)
    url = reverse("approval:request-action-detail", args=(request.id, action.id))

    response = api_request("put", url, {"operation": "skip"})
    assert response.status_code == 405

    response = api_request("patch", url, {"operation": "skip"})
    assert response.status_code == 405

    response = api_request("delete", url)
    assert response.status_code == 405
