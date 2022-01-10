""" Test population json template with input parameters """
import pytest

from ansible_catalog.main.catalog.tests.factories import (
    PortfolioItemFactory,
    ServicePlanFactory,
)
from ansible_catalog.main.inventory.tests.factories import (
    ServiceOfferingFactory,
    InventoryServicePlanFactory,
)
from ansible_catalog.main.catalog.services.compare_service_plans import (
    CompareServicePlans,
)


SCHEMA = {
    "schemaType": "emptySchema",
    "schema": {
        "fields": [
            {
                "component": "plain-text",
                "name": "empty-service-plan",
                "label": "This product requires no user input and is fully configured by the system.",
            }
        ]
    },
}


SCHEMA_1 = {
    "schemaType": "default",
    "schema": {
        "fields": [
            {
                "component": "plain-text",
                "name": "empty-service-plan",
                "label": "Empty Service plan configured by the system.",
                "helper_text": "The new added field",
            },
            {
                "label": "State",
                "name": "state",
                "initial_value": "",
                "helper_text": "The state where you live",
                "is_required": True,
                "component": "select-field",
                "options": [
                    {"label": "NJ", "value": "NJ"},
                    {"label": "PA", "value": "PA"},
                    {"label": "OK", "value": "OK"},
                ],
                "validate": [{"type": "required-validator"}],
            },
        ],
        "title": "",
        "description": "",
    },
}

SCHEMA_2 = {
    "schemaType": "default",
    "schema": {
        "fields": [
            {
                "component": "plain-text",
                "name": "empty-service-plan",
                "label": "Empty Service plan configured by the system.",
            },
            {
                "label": "Number of Job templates",
                "name": "dev_null",
                "initial_value": 8,
                "helper_text": "Number of Job templates on this workflow",
                "is_required": True,
                "component": "text-field",
                "type": "number",
                "data_type": "integer",
                "options": [{"label": "", "value": ""}],
                "validate": [
                    {"type": "required-validator"},
                    {"type": "min-number-value", "value": 0},
                    {"type": "max-number-value", "value": 100},
                ],
            },
        ],
        "title": "",
        "description": "",
    },
}


SCHEMA_3 = {
    "schemaType": "default",
    "schema": {
        "fields": [
            {
                "name": "empty-service-plan",
                "label": "Empty Service plan configured by the system.",
            },
            {
                "label": "Number of Job templates",
                "name": "dev_null",
                "initial_value": 8,
                "helper_text": "Number of Job templates on this workflow",
                "component": "text-field",
                "type": "number",
                "data_type": "integer",
                "options": [{"label": "", "value": ""}],
                "validate": [
                    {"type": "required-validator"},
                    {"type": "min-number-value", "value": 0},
                    {"type": "max-number-value", "value": 100},
                ],
            },
        ],
        "title": "",
        "description": "",
    },
}


@pytest.mark.django_db
def test_is_outdated_with_empty_schema():
    service_plan = ServicePlanFactory(base_schema=SCHEMA, base_sha256="SCHEMA")

    assert CompareServicePlans.is_outdated(service_plan) is False


@pytest.mark.django_db
def test_is_outdated_with_same_schema():
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=SCHEMA_1,
        schema_sha256="SCHEMA_1",
    )

    service_plan = ServicePlanFactory(
        service_offering_ref=str(service_offering.id),
        base_schema=SCHEMA_1,
        base_sha256="SCHEMA_1",
    )

    assert CompareServicePlans.is_outdated(service_plan) is False


@pytest.mark.django_db
def test_is_outdated_with_different_schemas_when_modified_is_true():
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=SCHEMA_2,
        schema_sha256="SCHEMA_2",
    )

    service_plan = ServicePlanFactory(
        service_offering_ref=str(service_offering.id),
        base_schema=SCHEMA_1,
        base_sha256="SCHEMA_1",
        modified_schema=SCHEMA,
    )

    assert CompareServicePlans.is_outdated(service_plan) is True


@pytest.mark.django_db
def test_is_outdated_with_different_schemas_when_modified_is_false():
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=SCHEMA_2,
        schema_sha256="SCHEMA_2",
    )

    service_plan = ServicePlanFactory(
        service_offering_ref=str(service_offering.id),
        base_schema=SCHEMA_1,
        base_sha256="SCHEMA_1",
    )

    assert CompareServicePlans.is_outdated(service_plan) is False
    assert service_plan.base_schema == SCHEMA_2
    assert service_plan.modified_schema is None
    assert service_plan.base_sha256 == "SCHEMA_2"


@pytest.mark.django_db
def test_any_changed_with_changed_plans():
    service_offering = ServiceOfferingFactory(survey_enabled=True)

    InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=SCHEMA_2,
        schema_sha256="SCHEMA_2",
    )

    plan1 = ServicePlanFactory(
        service_offering_ref=str(service_offering.id),
        base_schema=SCHEMA,
        base_sha256="SCHEMA",
    )
    plan2 = ServicePlanFactory(
        service_offering_ref=str(service_offering.id),
        base_schema=SCHEMA_1,
        base_sha256="SCHEMA_1",
    )
    plan3 = ServicePlanFactory(
        service_offering_ref=str(service_offering.id),
        base_schema=SCHEMA_2,
        base_sha256="SCHEMA_1",
        modified_schema=SCHEMA_1,
    )

    assert CompareServicePlans.any_changed([plan1, plan2, plan3]) is True


@pytest.mark.django_db
def test_any_changed_with_unchanged_plans():
    service_offering = ServiceOfferingFactory(survey_enabled=True)

    InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=SCHEMA_2,
        schema_sha256="SCHEMA_2",
    )

    plan1 = ServicePlanFactory(
        service_offering_ref=str(service_offering.id),
        base_schema=SCHEMA_2,
        base_sha256="SCHEMA_2",
    )
    plan2 = ServicePlanFactory(
        service_offering_ref=str(service_offering.id),
        base_schema=SCHEMA_2,
        base_sha256="SCHEMA_2",
    )
    plan3 = ServicePlanFactory(
        service_offering_ref=str(service_offering.id),
        base_schema=SCHEMA_2,
        base_sha256="SCHEMA_2",
    )

    assert CompareServicePlans.any_changed([plan1, plan2, plan3]) is False


@pytest.mark.django_db
def test_changed_plans_with_changes():
    service_offering = ServiceOfferingFactory(survey_enabled=True)

    InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=SCHEMA_2,
        schema_sha256="SCHEMA_2",
    )

    plan1 = ServicePlanFactory(
        service_offering_ref=str(service_offering.id),
        base_schema=SCHEMA_3,
        base_sha256="SCHEMA_3",
        modified_schema=SCHEMA,
    )
    plan2 = ServicePlanFactory(
        service_offering_ref=str(service_offering.id),
        base_schema=SCHEMA_2,
        base_sha256="SCHEMA_2",
    )
    plan3 = ServicePlanFactory(
        service_offering_ref=str(service_offering.id),
        base_schema=SCHEMA_2,
        base_sha256="SCHEMA_2",
    )

    assert CompareServicePlans.changed_plans([plan1, plan2, plan3]) == [plan1]
    assert plan1.outdated is True
    assert plan2.outdated is False
    assert plan3.outdated is False
    assert (
        plan1.outdated_changes
        == "Schema fields changes have been detected: fields changed: ['empty-service-plan', 'dev_null']"
    )


@pytest.mark.django_db
def test_changed_plans_with_unchanges():
    service_offering = ServiceOfferingFactory(survey_enabled=True)

    InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=SCHEMA_2,
        schema_sha256="SCHEMA_2",
    )

    plan1 = ServicePlanFactory(
        service_offering_ref=str(service_offering.id),
        base_schema=SCHEMA_2,
        base_sha256="SCHEMA_2",
    )
    plan2 = ServicePlanFactory(
        service_offering_ref=str(service_offering.id),
        base_schema=SCHEMA_2,
        base_sha256="SCHEMA_2",
    )

    assert CompareServicePlans.changed_plans([plan1, plan2]) == []


@pytest.mark.django_db
def test_changed_plans_with_changed_fields():
    service_offering = ServiceOfferingFactory(survey_enabled=True)

    InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=SCHEMA_2,
        schema_sha256="SCHEMA_2",
    )

    plan = ServicePlanFactory(
        service_offering_ref=str(service_offering.id),
        base_schema=SCHEMA_1,
        base_sha256="SCHEMA_1",
        modified_schema=SCHEMA,
    )

    assert CompareServicePlans.is_outdated(plan) is True
    assert plan.outdated is True
    assert (
        "fields added: ['dev_null']; fields removed: ['state']; fields changed: ['empty-service-plan']"
        in plan.outdated_changes
    )


@pytest.mark.django_db
def test_is_empty_with_empty_schema():
    service_plan = ServicePlanFactory(base_schema=SCHEMA)
    assert CompareServicePlans.is_empty(service_plan) is True


@pytest.mark.django_db
def test_is_empty_with_valid_schema():
    service_plan = ServicePlanFactory(base_schema=SCHEMA_1)
    assert CompareServicePlans.is_empty(service_plan) is False
