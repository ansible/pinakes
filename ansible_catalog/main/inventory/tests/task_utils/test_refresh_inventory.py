""" Module to test the Refresh Inventory. """
from unittest.mock import patch
import pytest
from ansible_catalog.main.tests.factories import TenantFactory
from ansible_catalog.main.inventory.tests.factories import SourceFactory
from ansible_catalog.main.inventory.task_utils.refresh_inventory import (
    RefreshInventory,
)


class TestRefreshInventory:
    """Refresh Inventory Class."""

    @patch(
        "ansible_catalog.main.inventory.task_utils.refresh_inventory.ServiceOfferingNodeImport",
        autoSpec=True,
    )
    @patch(
        "ansible_catalog.main.inventory.task_utils.refresh_inventory.ServiceInventoryImport",
        autoSpec=True,
    )
    @patch(
        "ansible_catalog.main.inventory.task_utils.refresh_inventory.ServiceOfferingImport",
        autoSpec=True,
    )
    @pytest.mark.django_db
    def test_process(self, mock1, mock2, mock3):
        """Test the process method"""
        tenant = TenantFactory()
        source = SourceFactory(tenant=tenant)
        refresh_inventory = RefreshInventory(tenant.id, source.id)
        refresh_inventory.process()
        assert (mock1.return_value.process.call_count) == 1
        assert (mock2.return_value.process.call_count) == 1
        assert (mock3.return_value.process.call_count) == 1
