""" Module to test the Refresh Inventory. """
from unittest.mock import patch
from unittest import mock
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
        source_instance = SourceFactory(tenant=tenant)
        refresh_inventory = RefreshInventory(tenant.id, source_instance.id)
        refresh_inventory.process()
        assert (mock1.return_value.process.call_count) == 1
        assert (mock2.return_value.process.call_count) == 1
        assert (mock3.return_value.process.call_count) == 1

        source_instance.refresh_from_db()
        assert source_instance.refresh_started_at is not None
        assert source_instance.refresh_finished_at is not None
        assert source_instance.last_successful_refresh_at is not None
        assert source_instance.last_refresh_message is not None
        assert source_instance.refresh_state == source_instance.State.DONE

    @pytest.mark.django_db
    def test_last_refresh_message(self, mocker):
        tenant = TenantFactory()
        source_instance = SourceFactory(tenant=tenant)
        refresh_inventory = RefreshInventory(tenant.id, source_instance.id)

        mock1 = mock.Mock()
        mock2 = mock.Mock()
        mock3 = mock.Mock()
        mocker.patch(
            "ansible_catalog.main.inventory.task_utils.refresh_inventory.ServiceInventoryImport",
            return_value=mock1,
        )
        mocker.patch(
            "ansible_catalog.main.inventory.task_utils.refresh_inventory.ServiceOfferingImport",
            return_value=mock2,
        )
        mocker.patch(
            "ansible_catalog.main.inventory.task_utils.refresh_inventory.ServiceOfferingNodeImport",
            return_value=mock3,
        )
        test_suites = [
            [
                {
                    "added": 0,
                    "updated": 0,
                    "deleted": 0,
                },  # ServiceInventoryImport
                {
                    "added": 0,
                    "updated": 0,
                    "deleted": 0,
                },  # ServiceOfferingImport
                {
                    "added": 0,
                    "updated": 0,
                    "deleted": 0,
                },  # ServiceOfferingNodeImport
                "Nothing to update",  # last refresh message
            ],
            [
                {
                    "added": 1,
                    "updated": 0,
                    "deleted": 0,
                },  # ServiceInventoryImport
                {
                    "added": 0,
                    "updated": 0,
                    "deleted": 0,
                },  # ServiceOfferingImport
                {
                    "added": 0,
                    "updated": 0,
                    "deleted": 0,
                },  # ServiceOfferingNodeImport
                "Service Inventories: {'added': 1};\n",  # last refresh message
            ],
            [
                {
                    "added": 1,
                    "updated": 0,
                    "deleted": 0,
                },  # ServiceInventoryImport
                {
                    "added": 0,
                    "updated": 2,
                    "deleted": 0,
                },  # ServiceOfferingImport
                {
                    "added": 0,
                    "updated": 0,
                    "deleted": 3,
                },  # ServiceOfferingNodeImport
                "Service Inventories: {'added': 1};\nJob Templates & Workflows: {'updated': 2};\nWorkflow Template Nodes: {'deleted': 3}",  # last refresh message
            ],
        ]

        for suite in test_suites:
            mock1.get_stats.return_value = suite[0]
            mock2.get_stats.return_value = suite[1]
            mock3.get_stats.return_value = suite[2]

            refresh_inventory.process()
            source_instance.refresh_from_db()

            assert source_instance.last_refresh_message == suite[3]

    @patch(
        "ansible_catalog.main.inventory.task_utils.refresh_inventory.ServiceInventoryImport",
        side_effect=Exception("Failed to import inventory"),
    )
    @pytest.mark.django_db
    def test_process_with_exception(self, mocker):
        """Test the process method"""
        tenant = TenantFactory()
        source_instance = SourceFactory(tenant=tenant)

        refresh_inventory = RefreshInventory(tenant.id, source_instance.id)
        refresh_inventory.process()

        source_instance.refresh_from_db()
        assert source_instance.refresh_started_at is not None
        assert source_instance.refresh_finished_at is not None
        assert source_instance.last_successful_refresh_at is None
        assert source_instance.last_refresh_message.startswith(
            "Error: Failed to import inventory"
        )
        assert source_instance.refresh_state == source_instance.State.FAILED
