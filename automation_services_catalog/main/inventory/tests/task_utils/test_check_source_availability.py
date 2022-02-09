""" Module to test the source availability check. """
from unittest import mock

import pytest
from automation_services_catalog.main.tests.factories import TenantFactory
from automation_services_catalog.main.inventory.tests.factories import SourceFactory
from automation_services_catalog.main.inventory.task_utils.check_source_availability import (
    CheckSourceAvailability,
)
from automation_services_catalog.main.inventory.task_utils.controller_config import (
    ControllerConfig,
)


@pytest.mark.django_db
def test_process(mocker):
    """Test the process method"""
    tenant = TenantFactory()
    source_instance = SourceFactory(tenant=tenant)

    config = mock.Mock(
        tower_info={"version": "4.1.0"},
        tower=mock.Mock(url="http://tower.com"),
    )
    mocker.patch.object(ControllerConfig, "process", return_value=config)

    svc = CheckSourceAvailability(tenant.id, source_instance.id)
    svc.process()

    source_instance.refresh_from_db()
    assert source_instance.last_available_at is not None
    assert source_instance.last_checked_at is not None
    assert source_instance.availability_status == "available"
    assert source_instance.availability_message == "Available"
    assert source_instance.info == {
        "version": "4.1.0",
        "url": "http://tower.com",
    }


@pytest.mark.django_db
def test_process_with_exception(mocker):
    """Test the process method"""
    tenant = TenantFactory()
    source_instance = SourceFactory(tenant=tenant)

    mocker.patch.object(
        ControllerConfig,
        "process",
        side_effect=Exception("Failed to get controller config"),
    )

    svc = CheckSourceAvailability(tenant.id, source_instance.id)
    svc.process()

    source_instance.refresh_from_db()
    assert source_instance.availability_status == "unavailable"
    assert source_instance.availability_message == "Unavailable"
