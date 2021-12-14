""" Module to test import of ServicePlan (tower SurveySpec). """

from unittest.mock import Mock
import pytest
from ansible_catalog.main.tests.factories import TenantFactory
from ansible_catalog.main.inventory.tests.factories import (
    SourceFactory,
    ServiceOfferingFactory,
)
from ansible_catalog.main.inventory.models import InventoryServicePlan
from ansible_catalog.main.inventory.task_utils.service_plan_import import (
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
        assert (InventoryServicePlan.objects.count()) == 1
        assert (
            InventoryServicePlan.objects.first().service_offering.id
        ) == service_offering.id
        assert InventoryServicePlan.objects.first().schema_sha256 is not None
