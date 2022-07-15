"""Module for testing Notification settings"""
import pytest
from pinakes.main.approval.models import NotificationType
from pinakes.main.approval.permissions import TemplatePermission
from pinakes.main.approval.tests.factories import NotificationSettingFactory


@pytest.mark.django_db
def test_notification_type_list(api_request, mocker):
    """Get a list of notification types"""
    has_permission = mocker.spy(TemplatePermission, "has_permission")
    response = api_request("get", "approval:notificationtype-list")

    assert response.status_code == 200
    assert response.data["count"] == 1  # seeded one
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_notification_type_retrieve(api_request, mocker):
    """RETRIEVE a notification type by its id"""
    has_permission = mocker.spy(TemplatePermission, "has_permission")
    notification = NotificationType.objects.first()
    response = api_request(
        "get", "approval:notificationtype-detail", notification.id
    )

    assert response.status_code == 200
    assert response.data["id"] == notification.id
    assert response.data["icon_url"] is not None
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_notification_type_not_supported_methods(api_request):
    """PUT on a notification type should fail"""
    response = api_request(
        "put", "approval:notificationtype-detail", 1, {"name": "update"}
    )
    assert response.status_code == 405

    # PATCH on a notification type should fail
    response = api_request(
        "patch", "approval:notificationtype-detail", 1, {"name": "update"}
    )
    assert response.status_code == 405

    # DELETE on a notification type should fail
    response = api_request("delete", "approval:notificationtype-detail", 1)
    assert response.status_code == 405

    # POST on notifications type should fail
    response = api_request(
        "post",
        "approval:notificationtype-list",
        data={"n_type": "name", "setting_schema": {}},
    )
    assert response.status_code == 405


@pytest.mark.django_db
def test_notification_setting_list(api_request, mocker):
    """Get a list of notification settings"""
    has_permission = mocker.spy(TemplatePermission, "has_permission")
    NotificationSettingFactory()
    response = api_request("get", "approval:notificationsetting-list")

    assert response.status_code == 200
    assert response.data["count"] == 1
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_notification_setting_retrieve(api_request, mocker):
    """RETRIEVE a notification setting by its id"""
    has_permission = mocker.spy(TemplatePermission, "has_permission")
    notification = NotificationSettingFactory(settings={"key": "val"})
    response = api_request(
        "get", "approval:notificationsetting-detail", notification.id
    )

    assert response.status_code == 200
    assert response.data["id"] == notification.id
    assert response.data["notification_type"] > 0
    assert bool(response.data["name"]) is True
    assert response.data["settings"]["key"] == "val"

    has_permission.assert_called_once()


@pytest.mark.django_db
def test_notification_setting_delete(api_request, mocker):
    """Delete a notification setting"""
    has_permission = mocker.spy(TemplatePermission, "has_permission")
    notification = NotificationSettingFactory()
    response = api_request(
        "delete", "approval:notificationsetting-detail", notification.id
    )

    assert response.status_code == 204
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_notification_setting_patch(api_request, mocker):
    """Update a notification setting"""
    has_permission = mocker.spy(TemplatePermission, "has_permission")
    notification = NotificationSettingFactory()
    response = api_request(
        "patch",
        "approval:notificationsetting-detail",
        notification.id,
        {"settings": {"key": "newval"}},
    )

    assert response.status_code == 200
    assert response.data["settings"]["key"] == "newval"
    has_permission.assert_called_once()


@pytest.mark.django_db
def test_notification_setting_put_not_supported(api_request):
    """PUT on a notification setting should fail"""
    notification = NotificationSettingFactory()
    response = api_request(
        "put",
        "approval:notificationsetting-detail",
        notification.id,
        {"name": "update"},
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_notification_setting_post(api_request, mocker):
    """Create a notification"""
    has_permission = mocker.spy(TemplatePermission, "has_permission")
    notification_type = NotificationType.objects.first()
    data = {
        "name": "abcdef",
        "notification_type": notification_type.id,
        "settings": {"key": "val"},
    }
    response = api_request(
        "post",
        "approval:notificationsetting-list",
        data=data,
    )

    assert response.status_code == 201
    content = response.data
    assert content["name"] == "abcdef"
    assert content["notification_type"] == notification_type.id
    assert content["settings"]["key"] == "val"
    has_permission.assert_called_once()

    response = api_request(
        "post",
        "approval:notificationsetting-list",
        data=data,
    )
    # uniqueness
    assert response.status_code == 400
