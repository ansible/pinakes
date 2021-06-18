""" Module to test import of ServicePlan (tower SurveySpec). """

from unittest.mock import Mock
import pytest
from inventory.tests.factories import (
    TenantFactory,
    SourceFactory,
    ServiceOfferingFactory,
)
from inventory.models import ServicePlan
from inventory.task_utils.service_plan_import import ServicePlanImport


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
        assert (ServicePlan.objects.all().count()) == 1
        assert (ServicePlan.objects.first().service_offering.id) == service_offering.id
