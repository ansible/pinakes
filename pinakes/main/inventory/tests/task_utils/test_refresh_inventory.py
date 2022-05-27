"""Module to test the Refresh Inventory."""
from unittest.mock import patch
import pytest
from pinakes.main.tests.factories import TenantFactory
from pinakes.main.inventory.tests.factories import (
    SourceFactory,
)
from pinakes.main.inventory.task_utils.refresh_inventory import (
    RefreshInventory,
)


class TestRefreshInventory:
    """Refresh Inventory Class."""

    @patch(
        "pinakes.main.inventory.task_utils.refresh_inventory."
        "ServiceOfferingNodeImport",
        autoSpec=True,
    )
    @patch(
        "pinakes.main.inventory.task_utils.refresh_inventory."
        "ServiceInventoryImport",
        autoSpec=True,
    )
    @patch(
        "pinakes.main.inventory.task_utils.refresh_inventory."
        "ServiceOfferingImport",
        autoSpec=True,
    )
    @pytest.mark.django_db
    def test_process(self, mock1, mock2, mock3):
        """Test the process method"""
        tenant = TenantFactory()
        source_instance = SourceFactory(tenant=tenant)
        mock1.return_value.get_stats.return_value = {}
        mock2.return_value.get_stats.return_value = {}
        mock3.return_value.get_stats.return_value = {}

        refresh_inventory = RefreshInventory(source_instance.id)
        refresh_inventory.process()
        assert mock1.return_value.process.call_count == 1
        assert mock2.return_value.process.call_count == 1
        assert mock3.return_value.process.call_count == 1

        source_instance.refresh_from_db()
        assert source_instance.refresh_started_at is not None
        assert source_instance.refresh_finished_at is not None
        assert source_instance.last_successful_refresh_at is not None
        assert source_instance.last_refresh_message is not None
        assert source_instance.refresh_state == source_instance.State.DONE

    @patch(
        "pinakes.main.inventory.task_utils.refresh_inventory."
        "ServiceInventoryImport",
        side_effect=Exception("Failed to import inventory"),
    )
    @pytest.mark.django_db
    def test_process_with_exception(self, mocker):
        """Test the process method"""
        tenant = TenantFactory()
        source_instance = SourceFactory(tenant=tenant)

        refresh_inventory = RefreshInventory(source_instance.id)
        refresh_inventory.process()

        source_instance.refresh_from_db()
        assert source_instance.refresh_started_at is not None
        assert source_instance.refresh_finished_at is not None
        assert source_instance.last_successful_refresh_at is None
        assert source_instance.refresh_state == source_instance.State.FAILED
