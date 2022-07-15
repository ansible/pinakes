"""Module to test the source availability check."""
from unittest import mock

import pytest
from pinakes.main.tests.factories import TenantFactory
from pinakes.main.inventory.tests.factories import (
    SourceFactory,
)
from pinakes.main.inventory.task_utils.check_source_availability import (
    CheckSourceAvailability,
)
from pinakes.main.inventory.task_utils.controller_config import (
    ControllerConfig,
)


@pytest.mark.django_db
def test_process(mocker):
    """Test the process method"""
    tenant = TenantFactory()
    source_instance = SourceFactory(tenant=tenant)

    config = mock.Mock(
        tower_info={"version": "4.1.0", "install_uuid": "abcdef"},
        tower=mock.Mock(url="http://tower.com"),
    )
    mocker.patch.object(ControllerConfig, "process", return_value=config)

    svc = CheckSourceAvailability(source_instance.id)
    svc.process()

    source_instance.refresh_from_db()
    assert source_instance.last_available_at is not None
    assert source_instance.last_checked_at is not None
    assert source_instance.availability_status == "available"
    assert (
        source_instance.availability_message == "Check availability completed"
    )
    assert source_instance.info == {
        "version": "4.1.0",
        "url": "http://tower.com",
        "install_uuid": "abcdef",
    }


@pytest.mark.django_db
def test_process_with_exception(mocker):
    """Test the process method"""
    tenant = TenantFactory()
    source_instance = SourceFactory(tenant=tenant)
    err_msg = "Failed to get controller config"

    mocker.patch.object(
        ControllerConfig,
        "process",
        side_effect=Exception(err_msg),
    )

    svc = CheckSourceAvailability(source_instance.id)
    svc.process()

    source_instance.refresh_from_db()
    assert source_instance.availability_status == "unavailable"
    assert source_instance.availability_message == err_msg
    assert source_instance.refresh_state == "Failed"


@pytest.mark.django_db
def test_process_with_changed_source(mocker):
    """Test the process method"""
    tenant = TenantFactory()
    new_uuid = "12345678"
    new_url = "http://www.example.com"
    source_instance = SourceFactory(
        tenant=tenant,
        info={"install_uuid": "abcdef", "url": "http://tower.com"},
    )
    config = mock.Mock(
        tower_info={"version": "4.1.0", "install_uuid": new_uuid},
        tower=mock.Mock(url=new_url),
    )
    mocker.patch.object(ControllerConfig, "process", return_value=config)

    svc = CheckSourceAvailability(source_instance.id)
    svc.process()

    source_instance.refresh_from_db()
    assert source_instance.availability_status == "unavailable"
    assert (
        source_instance.availability_message
        == "Once assigned source cannot be changed"
    )
    assert source_instance.refresh_state == "Failed"
    assert (
        source_instance.error_code
        == type(source_instance).ErrorCode.SOURCE_CANNOT_BE_CHANGED
    )
    assert source_instance.error_dict["new_install_uuid"] == new_uuid
    assert source_instance.error_dict["new_url"] == new_url
