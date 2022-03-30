""" Module for testing Notification settings """
import pytest
from pinakes.main.approval.models import Notification
from pinakes.main.approval.permissions import TemplatePermission


@pytest.mark.django_db
def test_notification_list(api_request, mocker):
    """Get a list of templates"""
    has_permission = mocker.spy(TemplatePermission, "has_permission")
    response = api_request("get", "approval:notification-list")

    assert response.status_code == 200
    assert response.data["count"] == 1  # seeded one
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_notification_retrieve(api_request, mocker):
    """RETRIEVE a template by its id"""
    has_permission = mocker.spy(TemplatePermission, "has_permission")
    notification = Notification.objects.first()
    response = api_request(
        "get", "approval:notification-detail", notification.id
    )

    assert response.status_code == 200
    assert response.data["id"] == notification.id
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_notification_not_supported_methods(api_request):
    """PUT on a notification should fail"""
    response = api_request(
        "put", "approval:notification-detail", 1, {"name": "update"}
    )
    assert response.status_code == 405

    """PATCH on a notification should fail"""
    response = api_request(
        "patch", "approval:notification-detail", 1, {"name": "update"}
    )
    assert response.status_code == 405

    """DELETE on a notification should fail"""
    response = api_request("delete", "approval:notification-detail", 1)
    assert response.status_code == 405

    """POST on notifications should fail"""
    response = api_request(
        "post",
        "approval:notification-list",
        data={"name": "name", "setting_schema": {}},
    )
    assert response.status_code == 405
