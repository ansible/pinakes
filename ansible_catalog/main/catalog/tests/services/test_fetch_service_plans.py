""" Test population json template with input parameters """
import pytest
import json

from ansible_catalog.main.catalog.tests.factories import (
    PortfolioItemFactory,
    ServicePlanFactory,
)
from ansible_catalog.main.inventory.tests.factories import (
    ServiceOfferingFactory,
    InventoryServicePlanFactory,
)
from ansible_catalog.main.catalog.services.fetch_service_plans import (
    FetchServicePlans,
)
from ansible_catalog.main.catalog.models import ServicePlan


TEST_SCHEMA = {
    "shcemaType": "default",
    "schema": {
        "fields": [
            {
                "label": "Number of Job templates",
                "name": "dev_null",
                "initialValue": 8,
                "helperText": "Number of Job templates on this workflow",
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
def test_fetch_new_service_plans():
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )
    assert (
        ServicePlan.objects.filter(portfolio_item=portfolio_item).count() == 0
    )

    InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=TEST_SCHEMA,
        schema_sha256=TEST_SHA256,
    )

    svc = FetchServicePlans(portfolio_item)
    svc.process()

    assert len(svc.service_plans) == 1
    assert svc.service_plans[0].portfolio_item_id == portfolio_item.id
    assert svc.service_plans[0].service_offering_ref == str(
        service_offering.id
    )
    assert svc.service_plans[0].schema == TEST_SCHEMA

    assert (
        ServicePlan.objects.filter(portfolio_item=portfolio_item).count() == 1
    )


@pytest.mark.django_db
def test_fetch_existing_service_plans():
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )
    ServicePlanFactory(
        portfolio_item=portfolio_item,
        service_offering_ref=portfolio_item.service_offering_ref,
    )
    assert (
        ServicePlan.objects.filter(portfolio_item=portfolio_item).count() == 1
    )

    InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=TEST_SCHEMA,
        schema_sha256=TEST_SHA256,
    )

    svc = FetchServicePlans(portfolio_item)
    svc.process()

    assert len(svc.service_plans) == 1
    assert svc.service_plans[0].portfolio_item_id == portfolio_item.id
    assert svc.service_plans[0].service_offering_ref == str(
        service_offering.id
    )
    assert svc.service_plans[0].schema == TEST_SCHEMA

    assert (
        ServicePlan.objects.filter(portfolio_item=portfolio_item).count() == 1
    )
