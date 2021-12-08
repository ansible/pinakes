""" Test population json template with input parameters """
import pytest
import json

from ansible_catalog.main.catalog.tests.factories import (
    PortfolioItemFactory,
    CatalogServicePlanFactory,
)
from ansible_catalog.main.inventory.tests.factories import (
    ServiceOfferingFactory,
    ServicePlanFactory,
)
from ansible_catalog.main.catalog.services.reset_service_plan import (
    ResetServicePlan,
)


@pytest.mark.django_db
def test_reset_service_plan_with_schema():
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )
    schema = {
        "schema_type": "default",
        "schema": {
            "fields": [
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
                }
            ],
            "title": "",
            "description": "",
        },
    }
    ServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=schema,
    )
    catalog_service_plan = CatalogServicePlanFactory(
        portfolio_item=portfolio_item
    )

    svc = ResetServicePlan(catalog_service_plan).process()

    assert catalog_service_plan.schema == schema
    assert catalog_service_plan.modified is False
    assert catalog_service_plan.imported is True


@pytest.mark.django_db
def test_reset_service_plan_with_no_schema():
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )
    catalog_service_plan = CatalogServicePlanFactory(
        portfolio_item=portfolio_item
    )

    svc = ResetServicePlan(catalog_service_plan).process()

    assert catalog_service_plan.schema is None
    assert catalog_service_plan.modified is False
    assert catalog_service_plan.imported is True
