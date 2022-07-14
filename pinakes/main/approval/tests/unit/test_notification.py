"""Test NotificationType and NotificationSetting"""

import pytest
from cryptography.fernet import MultiFernet
from django.db import IntegrityError

from pinakes.main.approval.tests.factories import (
    NotificationSettingFactory,
    NotificationTypeFactory,
)


@pytest.mark.django_db
def test_notification_type_uniq():
    """NotificationType n_type must be unique"""
    notification_type = NotificationTypeFactory()

    constraint_name = (
        f"{notification_type._meta.app_label}_notification_type.n_type"
    )
    with pytest.raises(IntegrityError) as excinfo:
        NotificationTypeFactory(n_type=notification_type.n_type)
        assert f"UNIQUE constraint failed: {constraint_name}" in str(
            excinfo.value
        )


@pytest.mark.django_db
def test_notification_setting_name_uniq():
    """NotificationSetting name must be unique"""
    notification_setting = NotificationSettingFactory()

    constraint_name = (
        f"{notification_setting._meta.app_label}_notification_setting.name"
    )
    with pytest.raises(IntegrityError) as excinfo:
        NotificationSettingFactory(name=notification_setting.name)
        assert f"UNIQUE constraint failed: {constraint_name}" in str(
            excinfo.value
        )


@pytest.mark.django_db
def test_empty_notification_type():
    """NotificationType n_type can't be empty"""
    notification_type = NotificationTypeFactory()
    constraint_name = (
        f"{notification_type._meta.app_label}_notificationtype_n_type_empty"
    )
    with pytest.raises(IntegrityError) as excinfo:
        NotificationTypeFactory(n_type="")
    assert constraint_name in str(excinfo.value)


@pytest.mark.django_db
def test_empty_notification_setting():
    """NotificationSetting name can't be empty"""
    notification_setting = NotificationSettingFactory()
    constraint_name = (
        f"{notification_setting._meta.app_label}_notificationsetting_name"
        "_empty"
    )
    with pytest.raises(IntegrityError) as excinfo:
        NotificationSettingFactory(name="")
    assert constraint_name in str(excinfo.value)


@pytest.mark.django_db
def test_notification_setting_encryption(mocker):
    """NotificationSetting settings must be encrypted"""
    spy = mocker.spy(MultiFernet, "encrypt")
    NotificationSettingFactory(settings={"param": "val"})
    assert spy.call_count == 1
