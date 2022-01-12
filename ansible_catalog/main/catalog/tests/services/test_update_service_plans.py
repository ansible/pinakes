import pytest
from ansible_catalog.main.catalog.services.update_service_plans import (
    UpdateServicePlans,
)

from ansible_catalog.main.catalog.tests.factories import (
    PortfolioItemFactory,
    ServicePlanFactory,
)
from ansible_catalog.main.inventory.tests.factories import (
    ServiceOfferingFactory,
)
from ansible_catalog.main.inventory.tests.factories import (
    InventoryServicePlanFactory,
)

BASE_SCHEMA = {
    "schema_type": "default",
    "schema": {
        "fields": [
            {
                "name": "username",
                "label": "Name",
                "options": [{"label": "", "value": ""}],
                "validate": [
                    {"type": "required-validator"},
                    {"type": "min-length-validator", "threshold": 1},
                    {"type": "max-length-validator", "threshold": 25},
                ],
                "component": "text-field",
                "helper_text": "Name",
                "is_required": True,
                "initial_value": "",
            }
        ],
        "title": "",
        "description": "",
    },
}

# Looks like the BASE_SCHEMA but the max_length_validator is more restrictive
MODIFIED_SCHEMA = {
    "schema_type": "default",
    "schema": {
        "fields": [
            {
                "name": "username",
                "label": "Name",
                "options": [{"label": "", "value": ""}],
                "validate": [
                    {"type": "required-validator"},
                    {"type": "min-length-validator", "threshold": 1},
                    {"type": "max-length-validator", "threshold": 10},
                ],
                "component": "text-field",
                "helper_text": "Name",
                "is_required": True,
                "initial_value": "",
            }
        ],
        "title": "",
        "description": "",
    },
}
BASE_SHA256 = "12345678"

UPDATED_SCHEMA = {
    "schema_type": "default",
    "schema": {
        "fields": [
            {
                "name": "company",
                "label": "company",
                "options": [{"label": "", "value": ""}],
                "validate": [
                    {"type": "required-validator"},
                    {"type": "min-length-validator", "threshold": 1},
                    {"type": "max-length-validator", "threshold": 50},
                ],
                "component": "text-field",
                "helper_text": "Name",
                "is_required": True,
                "initial_value": "Red Hat Inc",
            }
        ],
        "title": "",
        "description": "",
    },
}
UPDATED_SHA256 = "567890"


def configure_test_sp(
    updated_schema=BASE_SCHEMA,
    updated_sha256=BASE_SHA256,
    base_schema=BASE_SCHEMA,
    base_sha256=BASE_SHA256,
    modified_schema=None,
    isp_id=None,
):
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    inventory_service_plan = InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=updated_schema,
        schema_sha256=updated_sha256,
    )

    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )

    if isp_id is None:
        isp_id = inventory_service_plan.id

    return ServicePlanFactory(
        portfolio_item=portfolio_item,
        service_offering_ref=portfolio_item.service_offering_ref,
        inventory_service_plan_ref=isp_id,
        modified_schema=modified_schema,
        base_sha256=base_sha256,
        base_schema=base_schema,
    )


@pytest.mark.django_db
def test_same_service_plan():
    service_plan = configure_test_sp()
    upd = UpdateServicePlans(service_plan.tenant_id, 1)
    upd.process()

    assert upd.updated == 0


@pytest.mark.django_db
def test_update_service_plan():
    service_plan = configure_test_sp(UPDATED_SCHEMA, UPDATED_SHA256)
    upd = UpdateServicePlans(service_plan.tenant_id, 1)
    upd.process()

    assert upd.updated == 1
    service_plan.refresh_from_db()
    assert service_plan.base_sha256 == UPDATED_SHA256


@pytest.mark.django_db
def test_modified_service_plan():
    service_plan = configure_test_sp(
        UPDATED_SCHEMA,
        UPDATED_SHA256,
        BASE_SCHEMA,
        BASE_SHA256,
        MODIFIED_SCHEMA,
    )
    upd = UpdateServicePlans(service_plan.tenant_id, 1)
    upd.process()

    service_plan.refresh_from_db()
    assert upd.updated == 1
    assert service_plan.outdated == True
