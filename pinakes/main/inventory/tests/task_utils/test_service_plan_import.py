"""Module to test import of ServicePlan (tower SurveySpec)."""

import json
import hashlib
from unittest.mock import Mock
import pytest
from pinakes.main.tests.factories import TenantFactory
from pinakes.main.inventory.tests.factories import (
    SourceFactory,
    ServiceOfferingFactory,
    InventoryServicePlanFactory,
)
from pinakes.main.inventory.models import (
    InventoryServicePlan,
)
from pinakes.main.inventory.task_utils.service_plan_import import (
    ServicePlanImport,
)


class TestServicePlanImport:
    """Class to test import of service plans."""

    @pytest.mark.django_db
    def test_add(self):
        """Test adding new objects."""
        tenant = TenantFactory()
        source = SourceFactory()
        service_offering = ServiceOfferingFactory(
            tenant=tenant, source=source, survey_enabled=True
        )

        tower_mock = Mock()
        objs = [{"name": "298", "desc": "Test Description", "spec": []}]

        def fake_method(*_args, **_kwarg):
            for i in objs:
                yield i

        tower_mock.get.side_effect = fake_method
        converter_mock = Mock()
        converter_mock.process.return_value = {"abc": 123}
        spi = ServicePlanImport(tenant, source, tower_mock, converter_mock)
        spi.process(
            f"/api/v2/survey_spec/{service_offering.source_ref}/",
            service_offering.id,
            service_offering.source_ref,
        )
        assert spi.get_stats()["adds"] == 1
        assert spi.get_stats()["updates"] == 0
        assert (InventoryServicePlan.objects.count()) == 1
        assert (
            InventoryServicePlan.objects.first().service_offering.id
        ) == service_offering.id
        assert InventoryServicePlan.objects.first().schema_sha256 is not None

    @pytest.mark.django_db
    def test_add_with_no_data(self):
        """Test adding new objects with empty response from tower."""
        tenant = TenantFactory()
        source = SourceFactory()
        service_offering = ServiceOfferingFactory(
            tenant=tenant, source=source, survey_enabled=True
        )

        tower_mock = Mock()
        objs = [{"name": None, "description": None}]

        def fake_method(*_args, **_kwarg):
            for i in objs:
                yield i

        tower_mock.get.side_effect = fake_method
        converter_mock = Mock()
        converter_mock.process.return_value = {"abc": 123}
        spi = ServicePlanImport(tenant, source, tower_mock, converter_mock)
        spi.process(
            f"/api/v2/survey_spec/{service_offering.source_ref}/",
            service_offering.id,
            service_offering.source_ref,
        )
        assert spi.get_stats()["adds"] == 0
        assert spi.get_stats()["updates"] == 0
        assert (InventoryServicePlan.objects.count()) == 0

    @pytest.mark.django_db
    def test_update(self):
        """Test updating survey objects."""
        old_spec = [{"name": "abc"}]
        old_survey_obj = {
            "name": "298",
            "desc": "Test Description",
            "spec": old_spec,
        }
        schema_sha256 = hashlib.sha256(
            json.dumps(old_survey_obj).encode()
        ).hexdigest()
        inventory_service_plan = InventoryServicePlanFactory(
            create_json_schema=old_spec, schema_sha256=schema_sha256
        )
        tenant = inventory_service_plan.tenant
        source = inventory_service_plan.source
        tower_mock = Mock()
        new_spec = [{"name": "fred"}]
        new_survey_obj = {
            "name": "298",
            "desc": "Test Description",
            "spec": new_spec,
        }
        new_schema_sha256 = hashlib.sha256(
            json.dumps(new_survey_obj).encode()
        ).hexdigest()
        objs = [new_survey_obj]

        def fake_method(*_args, **_kwarg):
            for i in objs:
                yield i

        tower_mock.get.side_effect = fake_method
        converter_mock = Mock()
        converter_mock.process.return_value = {"abc": 123}
        spi = ServicePlanImport(tenant, source, tower_mock, converter_mock)

        spi.process(
            f"/api/v2/survey_spec/{inventory_service_plan.source_ref}/",
            inventory_service_plan.id,
            inventory_service_plan.source_ref,
        )
        assert spi.get_stats()["adds"] == 0
        assert spi.get_stats()["updates"] == 1
        assert (InventoryServicePlan.objects.count()) == 1
        assert (
            InventoryServicePlan.objects.first().id
        ) == inventory_service_plan.id
        assert (
            InventoryServicePlan.objects.first().schema_sha256
            == new_schema_sha256
        )

    @pytest.mark.django_db
    def test_update_no_change(self):
        """Test updating survey objects with no change."""
        old_spec = [{"name": "abc"}]
        old_survey_obj = {
            "name": "298",
            "desc": "Test Description",
            "spec": old_spec,
        }
        schema_sha256 = hashlib.sha256(
            json.dumps(old_survey_obj).encode()
        ).hexdigest()
        inventory_service_plan = InventoryServicePlanFactory(
            create_json_schema=old_spec, schema_sha256=schema_sha256
        )
        tenant = inventory_service_plan.tenant
        source = inventory_service_plan.source
        tower_mock = Mock()
        objs = [old_survey_obj]

        def fake_method(*_args, **_kwarg):
            for i in objs:
                yield i

        tower_mock.get.side_effect = fake_method
        converter_mock = Mock()
        converter_mock.process.return_value = {"abc": 123}
        spi = ServicePlanImport(tenant, source, tower_mock, converter_mock)

        spi.process(
            f"/api/v2/survey_spec/{inventory_service_plan.source_ref}/",
            inventory_service_plan.id,
            inventory_service_plan.source_ref,
        )
        assert spi.get_stats()["adds"] == 0
        assert spi.get_stats()["updates"] == 0
        assert (InventoryServicePlan.objects.count()) == 1
        assert (
            InventoryServicePlan.objects.first().id
        ) == inventory_service_plan.id
        assert (
            InventoryServicePlan.objects.first().schema_sha256 == schema_sha256
        )
