"""Test population json template with input parameters"""
import pytest
import copy

from pinakes.main.catalog.tests.factories import (
    ServicePlanFactory,
)
from pinakes.main.inventory.tests.factories import (
    ServiceOfferingFactory,
    InventoryServicePlanFactory,
)
from pinakes.main.catalog.services.refresh_service_plan import (
    RefreshServicePlan,
)

TEST_SCHEMA = {
    "schemaType": "default",
    "schema": {
        "fields": [
            {
                "label": "Number of Job templates",
                "name": "dev_null",
                "initialValue": 8,
                "helper_text": "Number of Job templates on this workflow",
                "isRequired": True,
                "component": "text-field",
                "type": "number",
                "dataType": "integer",
                "options": [{"label": "", "value": ""}],
                "validate": [
                    {"type": "required-validator"},
                    {"type": "min-number-value", "value": 0},
                    {"type": "max-number-value", "value": 100},
                ],
            }
        ],
        "title": "",
        "description": "",
    },
}
TEST_SHA256 = "abc123"


@pytest.mark.django_db
def test_refresh_service_plan_from_remote_with_enabled_survey():
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    service_plan = ServicePlanFactory(
        service_offering_ref=str(service_offering.id)
    )

    remote_service_plan = InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=TEST_SCHEMA,
        schema_sha256=TEST_SHA256,
    )

    svc = RefreshServicePlan(service_plan)
    svc.process()

    assert service_plan.schema == TEST_SCHEMA
    assert service_plan.base_sha256 == TEST_SHA256
    assert service_plan.modified is False
    assert service_plan.outdated is False
    assert service_plan.name == remote_service_plan.name
    assert service_plan.inventory_service_plan_ref == str(
        remote_service_plan.id
    )


@pytest.mark.django_db
def test_refresh_service_plans_from_remote_with_disabled_survey():
    service_offering = ServiceOfferingFactory()
    service_plan = ServicePlanFactory(
        service_offering_ref=str(service_offering.id)
    )

    InventoryServicePlanFactory(
        service_offering=service_offering,
    )

    svc = RefreshServicePlan(service_plan)
    svc.process()

    assert service_plan.schema["schemaType"] == "emptySchema"
    assert service_plan.modified is False
    assert service_plan.outdated is False
    assert service_plan.name == ""
    assert service_plan.inventory_service_plan_ref == ""


@pytest.mark.django_db
def test_refresh_service_plans_with_empty_entities():
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    service_plan = ServicePlanFactory(
        service_offering_ref=str(service_offering.id)
    )
    svc = RefreshServicePlan(service_plan)
    svc.process()

    assert service_plan.schema is None
    assert service_plan.modified is False
    assert service_plan.outdated is False
    assert service_plan.name == ""
    assert service_plan.inventory_service_plan_ref == ""


@pytest.mark.django_db
def test_refresh_service_plan_with_modified_base():
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    modified_schama = {"schemaType": "custom"}
    service_plan = ServicePlanFactory(
        service_offering_ref=str(service_offering.id),
        base_schema=TEST_SCHEMA,
        base_sha256=TEST_SHA256,
        modified_schema=modified_schama,
    )

    remote_schema = copy.deepcopy(TEST_SCHEMA)
    remote_schema["schema"]["fields"][0]["initialValue"] = 10

    remote_service_plan = InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=remote_schema,
    )

    svc = RefreshServicePlan(service_plan)
    svc.process()

    assert service_plan.schema == modified_schama
    assert service_plan.modified is True
    assert service_plan.outdated is True
    assert len(service_plan.outdated_changes) > 0
    assert service_plan.name == remote_service_plan.name
    assert service_plan.inventory_service_plan_ref == str(
        remote_service_plan.id
    )
