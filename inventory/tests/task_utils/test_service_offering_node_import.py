""" Module to test import of service offering node """
from unittest.mock import Mock
import pytest

from inventory.task_utils.service_offering_node_import import ServiceOfferingNodeImport
from inventory.tests.factories import (
    TenantFactory,
    SourceFactory,
    ServiceInventoryFactory,
    ServiceOfferingFactory,
    ServiceOfferingNodeFactory,
)
from inventory.models import ServiceOfferingNode

class TestServiceOfferingNodeImport:
    """Test ServiceOfferingNode import"""

    @pytest.mark.django_db
    def test_add(self):
        """Test adding new objects."""
        tenant = TenantFactory()
        source = SourceFactory()
        inventory_source_ref = "999"
        inventory = ServiceInventoryFactory(
            tenant=tenant, source=source, source_ref=inventory_source_ref
        )
        service_offering = ServiceOfferingFactory(
            tenant=tenant, source=source, source_ref="298"
        )
        tower_mock = Mock()
        objs = [
            {
                "url": "/api/v2/workflow_job_template_nodes/298/",
                "id": 298,
                "summary_fields.unified_job_template.unified_job_type": "workflow_job",
                "created": "2021-06-10T15:59:33.431827Z",
                "modified": "2021-06-10T15:59:33.431850Z",
                "inventory": int(inventory_source_ref),
                "type": "workflow_job_template_node",
                "workflow_job_template": 298,
                "unified_job_template": 298,
            },
            {
                "url": "/api/v2/workflow_job_template_nodes/290/",
                "id": 290,
                "summary_fields.unified_job_template.unified_job_type": "job",
                "created": "2021-06-10T15:59:33.453817Z",
                "modified": "2021-06-10T15:59:33.453851Z",
                "inventory": int(inventory_source_ref),
                "type": "workflow_job_template_node",
                "workflow_job_template": 298,
                "unified_job_template": 290,
            },
        ]

        def fake_method(*args, **_kwarg):
            for i in objs:
                yield i

        tower_mock.get.side_effect = fake_method
        inventory_import_mock = Mock()
        inventory_import_mock.source_ref_to_id.return_value = inventory.id

        service_offering_import_mock = Mock()
        service_offering_import_mock.source_ref_to_id.return_value = service_offering.id

        soni = ServiceOfferingNodeImport(
            tenant,
            source,
            tower_mock,
            inventory_import_mock,
            service_offering_import_mock,
        )
        soni.process()
        assert (ServiceOfferingNode.objects.all().count()) == 2
        assert (soni.get_stats()["adds"]) == 2

    @pytest.mark.django_db
    def test_deletes(self):
        """Test deleting old objects."""
        tenant = TenantFactory()
        source = SourceFactory()
        inventory_source_ref = "999"
        ServiceOfferingNodeFactory(tenant=tenant, source=source)
        inventory = ServiceInventoryFactory(
            tenant=tenant, source=source, source_ref=inventory_source_ref
        )
        service_offering = ServiceOfferingFactory(
            tenant=tenant, source=source, source_ref="298"
        )
        tower_mock = Mock()
        objs = []

        def fake_method(*args, **_kwarg):
            for i in objs:
                yield i

        tower_mock.get.side_effect = fake_method
        inventory_import_mock = Mock()
        inventory_import_mock.source_ref_to_id.return_value = inventory.id

        service_offering_import_mock = Mock()
        service_offering_import_mock.source_ref_to_id.return_value = service_offering.id

        soni = ServiceOfferingNodeImport(
            tenant,
            source,
            tower_mock,
            inventory_import_mock,
            service_offering_import_mock,
        )
        soni.process()
        assert (ServiceOfferingNode.objects.all().count()) == 0
        assert (soni.get_stats()["deletes"]) == 1

    @pytest.mark.django_db
    def test_updates(self):
        """Test update existing objects."""
        tenant = TenantFactory()
        source = SourceFactory()
        inventory_source_ref = "999"
        service_offering_node = ServiceOfferingNodeFactory(tenant=tenant, source=source)
        inventory = ServiceInventoryFactory(
            tenant=tenant, source=source, source_ref=inventory_source_ref
        )
        tower_mock = Mock()
        objs = [
            {
                "url": f"/api/v2/workflow_job_template_nodes/{service_offering_node.source_ref}/",
                "id": int(service_offering_node.source_ref),
                "summary_fields.unified_job_template.unified_job_type": "workflow_job",
                "created": "2021-06-10T15:59:33.431827Z",
                "modified": "2021-06-10T15:59:33.431850Z",
                "inventory": int(inventory_source_ref),
                "type": "workflow_job_template_node",
                "workflow_job_template": int(
                    service_offering_node.service_offering.source_ref
                ),
                "unified_job_template": int(
                    service_offering_node.root_service_offering.source_ref
                ),
            },
        ]

        def fake_method(*args, **_kwarg):
            for i in objs:
                yield i

        tower_mock.get.side_effect = fake_method
        inventory_import_mock = Mock()
        inventory_import_mock.source_ref_to_id.return_value = inventory.id

        service_offering_import_mock = Mock()
        service_offering_import_mock.source_ref_to_id.return_value = (
            service_offering_node.service_offering.id
        )

        soni = ServiceOfferingNodeImport(
            tenant,
            source,
            tower_mock,
            inventory_import_mock,
            service_offering_import_mock,
        )
        soni.process()
        assert (ServiceOfferingNode.objects.all().count()) == 1
        assert (soni.get_stats()["updates"]) == 1
        assert (soni.get_stats()["deletes"]) == 0
