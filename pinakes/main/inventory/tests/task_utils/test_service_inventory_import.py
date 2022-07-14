"""Test module for ServiceInventoryImport"""
from unittest.mock import Mock
import pytest
from django.core.exceptions import ObjectDoesNotExist
from pinakes.main.inventory.task_utils.service_inventory_import import (
    ServiceInventoryImport,
)
from pinakes.main.inventory.tests.factories import (
    SourceFactory,
    ServiceInventoryFactory,
)
from pinakes.main.inventory.models import ServiceInventory
from pinakes.main.tests.factories import TenantFactory


class TestServiceInventoryImport:
    """Test class for ServiceInventoryImport."""

    def fake_new_inventory(self, *_args, **_kwargs):
        """Create a fake response object"""
        objs = [
            {
                "name": "Fred",
                "url": "/api/v1/inventory/298/",
                "id": 298,
                "description": "Bedrock Inventory",
                "created": "2021-05-19T17:21:37.130143Z",
                "modified": "2021-06-10T20:06:35.234167Z",
            },
            {
                "name": "Barney",
                "url": "/api/v1/inventory/299/",
                "id": 299,
                "description": "Bedrock Inventory",
                "created": "2021-05-19T17:56:37.130143Z",
                "modified": "2021-06-10T20:46:35.234167Z",
            },
        ]
        for i in objs:
            yield i

    @pytest.mark.django_db
    def test_add(self):
        """Test adding new objects."""
        tenant = TenantFactory()
        source = SourceFactory()
        tower_mock = Mock()
        sii = ServiceInventoryImport(tenant, source, tower_mock)
        tower_mock.get.side_effect = self.fake_new_inventory
        sii.process()
        assert (ServiceInventory.objects.all().count()) == 2
        assert (sii.get_stats().get("adds")) == 2

    @pytest.mark.django_db
    def test_delete(self):
        """Test deleting old objects."""
        tenant = TenantFactory()
        source = SourceFactory(tenant=tenant)
        service_inventory = ServiceInventoryFactory(
            tenant=tenant, source=source
        )
        assert (ServiceInventory.objects.all().count()) == 1
        tower_mock = Mock()
        sii = ServiceInventoryImport(tenant, source, tower_mock)
        tower_mock.get.side_effect = self.fake_new_inventory
        sii.process()
        assert (ServiceInventory.objects.all().count()) == 2
        assert (sii.get_stats().get("deletes")) == 1
        assert (sii.get_stats().get("adds")) == 2
        with pytest.raises(ObjectDoesNotExist):
            ServiceInventory.objects.get(pk=service_inventory.id)

    @pytest.mark.django_db
    def test_update(self):
        """Test updating existing objects."""
        tenant = TenantFactory()
        source = SourceFactory(tenant=tenant)
        service_inventory = ServiceInventoryFactory(
            tenant=tenant, source=source
        )
        service_inventory.source_ref = str(service_inventory.id)
        service_inventory.save()
        assert (ServiceInventory.objects.all().count()) == 1
        objs = [
            {
                "name": "Fred Flintstone",
                "url": f"/api/v1/inventory/{service_inventory.id}/",
                "id": service_inventory.id,
                "description": "Bedrock Inventory",
                "created": "2021-05-19T17:21:37.130143Z",
                "modified": "2021-06-10T20:06:35.234167Z",
            },
        ]
        tower_mock = Mock()
        sii = ServiceInventoryImport(tenant, source, tower_mock)

        def fake_method(*_args, **_kwarg):
            for i in objs:
                yield i

        tower_mock.get.side_effect = fake_method
        sii.process()
        service_inventory_reloaded = ServiceInventory.objects.get(
            pk=service_inventory.id
        )
        assert (service_inventory_reloaded.name) == "Fred Flintstone"
        assert (sii.get_stats().get("deletes")) == 0
        assert (sii.get_stats().get("adds")) == 0
        assert (sii.get_stats().get("updates")) == 1

    @pytest.mark.django_db
    def test_no_change(self):
        """Test no change."""
        tenant = TenantFactory()
        source = SourceFactory(tenant=tenant)
        service_inventory = ServiceInventoryFactory(
            tenant=tenant, source=source
        )
        source_ref = str(service_inventory.id)
        service_inventory.source_ref = source_ref
        service_inventory.save()
        assert (ServiceInventory.objects.all().count()) == 1
        objs = [
            {
                "name": "Fred Flintstone",
                "url": f"/api/v1/inventory/{service_inventory.id}/",
                "id": service_inventory.id,
                "description": "Bedrock Inventory",
                "created": "2021-05-19T17:21:37.130143Z",
                "modified": str(service_inventory.source_updated_at),
            },
        ]
        tower_mock = Mock()
        sii = ServiceInventoryImport(tenant, source, tower_mock)

        def fake_method(*_args, **_kwarg):
            for i in objs:
                yield i

        tower_mock.get.side_effect = fake_method
        sii.process()
        service_inventory_reloaded = ServiceInventory.objects.get(
            pk=service_inventory.id
        )
        assert (service_inventory_reloaded.name) != "Fred Flintstone"
        assert (sii.source_ref_to_id(source_ref)) == service_inventory.id
        assert (sii.get_stats().get("deletes")) == 0
        assert (sii.get_stats().get("adds")) == 0
        assert (sii.get_stats().get("updates")) == 0
