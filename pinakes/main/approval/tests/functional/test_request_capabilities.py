import pytest
from pinakes.main.approval.tests.factories import RequestFactory
from pinakes.main.approval.permissions import WorkflowPermission


@pytest.mark.parametrize(
    ("state", "cancellable"),
    [
        ("pending", True),
        ("started", True),
        ("notified", True),
        ("completed", False),
        ("failed", False),
        ("skipped", False),
        ("canceled", False),
    ],
)
@pytest.mark.django_db
def test_request_capabilities_owner(
    api_request, mocker, normal_user, state, cancellable
):
    mocker.patch.object(
        WorkflowPermission, "has_permission", return_value=False
    )
    request = RequestFactory(user=normal_user, state=state)
    response = api_request(
        "get", "approval:request-detail", request.id, user=normal_user
    )

    assert response.data["metadata"]["user_capabilities"] == {
        "retrieve": True,
        "content": True,
        "cancel": cancellable,
    }


@pytest.mark.django_db
def test_child_request_capabilities_owner(api_request, mocker, normal_user):
    mocker.patch.object(
        WorkflowPermission, "has_permission", return_value=False
    )
    parent = RequestFactory(user=normal_user)
    request = RequestFactory(user=normal_user, parent=parent)
    response = api_request(
        "get", "approval:request-detail", request.id, user=normal_user
    )

    assert response.data["metadata"]["user_capabilities"] == {
        "retrieve": True,
        "content": True,
        "cancel": False,
    }


@pytest.mark.parametrize(
    ("state", "actionable"),
    [
        ("pending", False),
        ("started", False),
        ("notified", True),
        ("completed", False),
        ("failed", False),
        ("skipped", False),
        ("canceled", False),
    ],
)
@pytest.mark.django_db
def test_request_capabilities_approver(
    api_request, mocker, normal_user, state, actionable
):
    mocker.patch.object(
        WorkflowPermission, "has_permission", return_value=False
    )
    request = RequestFactory(state=state)
    response = api_request(
        "get", "approval:request-detail", request.id, user=normal_user
    )

    assert response.data["metadata"]["user_capabilities"] == {
        "retrieve": True,
        "content": True,
        "approve": actionable,
        "deny": actionable,
        "memo": True,
    }


@pytest.mark.django_db
def test_parent_request_capabilities_approver(
    api_request, mocker, normal_user
):
    mocker.patch.object(
        WorkflowPermission, "has_permission", return_value=False
    )
    request = RequestFactory(state="notified", number_of_children=2)
    response = api_request(
        "get", "approval:request-detail", request.id, user=normal_user
    )

    assert response.data["metadata"]["user_capabilities"] == {
        "retrieve": True,
        "content": True,
        "approve": False,
        "deny": False,
        "memo": True,
    }


@pytest.mark.django_db
def test_request_capabilities_admin(api_request):
    request = RequestFactory()
    response = api_request("get", "approval:request-detail", request.id)

    assert response.data["metadata"]["user_capabilities"] == {
        "retrieve": True,
        "content": True,
        "cancel": True,
        "approve": False,
        "deny": False,
        "memo": True,
    }
