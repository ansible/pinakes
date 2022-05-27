"""Test module for ServiceOfferingImport"""
from unittest.mock import Mock

import pytest

from pinakes.main.inventory.task_utils.service_offering_import import (
    ServiceOfferingImport,
    OfferingKind,
)
from pinakes.main.inventory.tests.factories import (
    InventoryServicePlanFactory,
    SourceFactory,
    ServiceInventoryFactory,
    ServiceOfferingFactory,
)
from pinakes.main.inventory.models import (
    InventoryServicePlan,
    ServiceOffering,
)
from pinakes.main.tests.factories import TenantFactory


class TestServiceOfferingImport:
    """Test class for ServiceOfferingImport."""

    @pytest.mark.django_db
    def test_add(self):
        """Test adding new objects."""
        tenant = TenantFactory()
        source = SourceFactory()
        inventory_source_ref = "999"
        inventory = ServiceInventoryFactory(
            tenant=tenant, source=source, source_ref=inventory_source_ref
        )
        tower_mock = Mock()
        template_objs = [
            {
                "name": "Fred",
                "url": "/api/v2/job_templates/298/",
                "id": 298,
                "description": "Bedrock Template",
                "created": "2021-05-19T17:21:37.130143Z",
                "modified": "2021-06-10T20:06:35.234167Z",
                "related.inventory": (
                    f"/api/v2/inventories/{inventory_source_ref}/"
                ),
                "related.survey_spec": "/api/v2/survey_spec/298",
                "survey_enabled": True,
                "type": "job_template",
            },
        ]
        workflow_objs = [
            {
                "name": "Barney",
                "url": "/api/v2/job_templates/299/",
                "id": 299,
                "description": "Barney Template",
                "created": "2021-05-19T17:56:37.130143Z",
                "modified": "2021-06-10T20:46:35.234167Z",
                "related.inventory": (
                    f"/api/v2/inventories/{inventory_source_ref}/"
                ),
                "survey_enabled": False,
                "related.survey_spec": "/api/v2/survey_spec/299",
                "type": "workflow_job_template",
            },
        ]

        def fake_method(*args, **_kwarg):
            if "workflow_job_templates" in args[0]:
                for i in workflow_objs:
                    yield i
            else:
                for i in template_objs:
                    yield i

        surveys = []

        def survey_requests(*args, **_kwarg):
            surveys.append(args[0])

        tower_mock.get.side_effect = fake_method
        inventory_import_mock = Mock()
        inventory_import_mock.source_ref_to_id.return_value = inventory.id
        plan_import_mock = Mock()
        plan_import_mock.process.side_effect = survey_requests

        soi = ServiceOfferingImport(
            tenant, source, tower_mock, inventory_import_mock, plan_import_mock
        )
        soi.process()
        assert (ServiceOffering.objects.all().count()) == 2
        assert (
            ServiceOffering.objects.first().service_inventory.id
        ) == inventory.id
        assert (soi.get_stats().get("adds")) == 2
        assert (len(surveys)) == 1

    @pytest.mark.django_db
    def test_update(self):
        """Test update existing objects."""
        tenant = TenantFactory()
        source = SourceFactory()
        inventory = ServiceInventoryFactory(tenant=tenant, source=source)
        inventory_source_ref = "999"
        inventory.source_ref = inventory_source_ref
        inventory.save()
        service_offering_source_ref = "997"
        ServiceOfferingFactory(
            tenant=tenant,
            source=source,
            service_inventory=inventory,
            kind=OfferingKind.JOB_TEMPLATE,
            source_ref=service_offering_source_ref,
        )
        tower_mock = Mock()
        template_objs = [
            {
                "name": "Fred",
                "url": f"/api/v2/job_templates/{service_offering_source_ref}/",
                "id": int(service_offering_source_ref),
                "description": "Bedrock Template",
                "created": "2021-05-19T17:21:37.130143Z",
                "modified": "2021-06-10T20:06:35.234167Z",
                "related.inventory": (
                    f"/api/v2/inventories/{inventory_source_ref}/"
                ),
                "related.survey_spec": (
                    f"/api/v2/survey_spec/{service_offering_source_ref}"
                ),
                "survey_enabled": True,
                "type": "job_template",
            },
        ]
        workflow_objs = []

        def fake_method(*args, **_kwarg):
            if "workflow_job_templates" in args[0]:
                for i in workflow_objs:
                    yield i
            else:
                for i in template_objs:
                    yield i

        surveys = []

        def survey_requests(*args, **_kwarg):
            surveys.append(args[0])

        tower_mock.get.side_effect = fake_method
        inventory_import_mock = Mock()
        inventory_import_mock.source_ref_to_id.return_value = inventory.id
        plan_import_mock = Mock()
        plan_import_mock.process.side_effect = survey_requests

        soi = ServiceOfferingImport(
            tenant, source, tower_mock, inventory_import_mock, plan_import_mock
        )
        soi.process()
        assert (ServiceOffering.objects.all().count()) == 1
        obj = ServiceOffering.objects.first()
        assert (obj.service_inventory.id) == inventory.id
        assert (obj.name) == "Fred"
        assert (obj.description) == "Bedrock Template"
        assert (soi.get_stats().get("updates")) == 1
        assert (len(surveys)) == 1

    @pytest.mark.django_db
    def test_delete(self):
        """Test delete existing objects."""
        tenant = TenantFactory()
        source = SourceFactory()
        inventory = ServiceInventoryFactory(tenant=tenant, source=source)
        inventory_source_ref = "999"
        inventory.source_ref = inventory_source_ref
        inventory.save()
        service_offering_source_ref = "997"
        ServiceOfferingFactory(
            tenant=tenant,
            source=source,
            service_inventory=inventory,
            kind=OfferingKind.JOB_TEMPLATE,
            source_ref=service_offering_source_ref,
        )
        tower_mock = Mock()
        template_objs = []
        workflow_objs = []

        def fake_method(*args, **_kwarg):
            if "workflow_job_templates" in args[0]:
                for i in workflow_objs:
                    yield i
            else:
                for i in template_objs:
                    yield i

        tower_mock.get.side_effect = fake_method
        inventory_import_mock = Mock()
        plan_import_mock = Mock()

        soi = ServiceOfferingImport(
            tenant, source, tower_mock, inventory_import_mock, plan_import_mock
        )
        soi.process()
        assert (ServiceOffering.objects.all().count()) == 0
        assert (soi.get_stats().get("deletes")) == 1

    @pytest.mark.django_db
    def test_update_survey_disabled(self):
        """Test update existing objects but survey is disabled."""
        tenant = TenantFactory()
        source = SourceFactory(tenant=tenant)
        service_inventory = ServiceInventoryFactory(
            source=source, tenant=tenant
        )
        service_offering = ServiceOfferingFactory(
            source=source,
            tenant=tenant,
            service_inventory=service_inventory,
            survey_enabled=True,
        )
        InventoryServicePlanFactory(
            tenant=tenant,
            source=source,
            service_offering=service_offering,
            source_ref=service_offering.source_ref,
        )

        tower_mock = Mock()
        template_objs = [
            {
                "name": "Fred",
                "url": f"/api/v2/job_templates/{service_offering.source_ref}/",
                "id": int(service_offering.source_ref),
                "description": "Bedrock Template",
                "created": "2021-05-19T17:21:37.130143Z",
                "modified": "2021-06-10T20:06:35.234167Z",
                "related.inventory": (
                    f"/api/v2/inventories/{service_inventory.source_ref}/"
                ),
                "related.survey_spec": (
                    f"/api/v2/survey_spec/{service_offering.source_ref}"
                ),
                "survey_enabled": False,
                "type": "job_template",
            },
        ]
        workflow_objs = []

        def fake_method(*args, **_kwarg):
            if "workflow_job_templates" in args[0]:
                for i in workflow_objs:
                    yield i
            else:
                for i in template_objs:
                    yield i

        surveys = []

        def survey_requests(*args, **_kwarg):
            surveys.append(args[0])

        tower_mock.get.side_effect = fake_method
        inventory_import_mock = Mock()
        inventory_import_mock.source_ref_to_id.return_value = (
            service_inventory.id
        )
        plan_import_mock = Mock()
        plan_import_mock.process.side_effect = survey_requests

        soi = ServiceOfferingImport(
            tenant, source, tower_mock, inventory_import_mock, plan_import_mock
        )
        soi.process()
        assert (ServiceOffering.objects.all().count()) == 1
        obj = ServiceOffering.objects.first()
        assert (obj.service_inventory.id) == service_inventory.id
        assert (obj.name) == "Fred"
        assert (obj.description) == "Bedrock Template"
        assert (soi.get_stats().get("updates")) == 1
        assert (len(surveys)) == 0
        assert (InventoryServicePlan.objects.all().count()) == 0
        assert (
            soi.source_ref_to_id(service_offering.source_ref)
        ) == service_offering.id

    @pytest.mark.django_db
    def test_none_related_inventory(self):
        """Test adding new objects."""
        tenant = TenantFactory()
        source = SourceFactory()
        inventory_source_ref = "999"
        inventory = ServiceInventoryFactory(
            tenant=tenant, source=source, source_ref=inventory_source_ref
        )
        tower_mock = Mock()
        template_objs = [
            {
                "name": "Fred",
                "url": "/api/v2/job_templates/298/",
                "id": 298,
                "description": "Bedrock Template",
                "created": "2021-05-19T17:21:37.130143Z",
                "modified": "2021-06-10T20:06:35.234167Z",
                "related.inventory": None,
                "related.survey_spec": "/api/v2/survey_spec/298",
                "survey_enabled": True,
                "type": "job_template",
            },
        ]
        workflow_objs = [
            {
                "name": "Barney",
                "url": "/api/v2/job_templates/299/",
                "id": 299,
                "description": "Barney Template",
                "created": "2021-05-19T17:56:37.130143Z",
                "modified": "2021-06-10T20:46:35.234167Z",
                "related.inventory": (
                    f"/api/v2/inventories/{inventory_source_ref}/"
                ),
                "survey_enabled": False,
                "related.survey_spec": "/api/v2/survey_spec/299",
                "type": "workflow_job_template",
            },
        ]

        def fake_method(*args, **_kwarg):
            if "workflow_job_templates" in args[0]:
                for i in workflow_objs:
                    yield i
            else:
                for i in template_objs:
                    yield i

        surveys = []

        def survey_requests(*args, **_kwarg):
            surveys.append(args[0])

        tower_mock.get.side_effect = fake_method
        inventory_import_mock = Mock()
        inventory_import_mock.source_ref_to_id.return_value = inventory.id
        plan_import_mock = Mock()
        plan_import_mock.process.side_effect = survey_requests

        soi = ServiceOfferingImport(
            tenant, source, tower_mock, inventory_import_mock, plan_import_mock
        )
        soi.process()
        assert (ServiceOffering.objects.all().count()) == 2
        assert (soi.get_stats().get("adds")) == 2
        assert (len(surveys)) == 1
