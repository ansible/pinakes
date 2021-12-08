""" Test population json template with input parameters """
import pytest
import json

from ansible_catalog.main.catalog.tests.factories import (
    PortfolioItemFactory,
    CatalogServicePlanFactory,
)
from ansible_catalog.main.inventory.tests.factories import (
    ServiceOfferingFactory,
    InventoryServicePlanFactory,
)
from ansible_catalog.main.catalog.services.import_service_plan import (
    ImportServicePlan,
)
from ansible_catalog.main.catalog.exceptions import (
    ServicePlanImportedException,
)


@pytest.mark.django_db
def test_import_service_plan_from_remote_with_enabled_survey():
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
    InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=schema,
    )

    svc = ImportServicePlan(portfolio_item)
    svc.process()

    assert svc.imported_service_plan.portfolio_item_id == portfolio_item.id
    assert svc.imported_service_plan.service_offering_ref == str(
        service_offering.id
    )
    assert svc.imported_service_plan.schema == schema
    assert svc.imported_service_plan.imported is True


@pytest.mark.django_db
def test_import_service_plans_from_remote_with_disabled_survey():
    service_offering = ServiceOfferingFactory()
    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )

    InventoryServicePlanFactory(
        service_offering=service_offering,
    )

    svc = ImportServicePlan(portfolio_item)
    svc.process()

    assert svc.imported_service_plan.portfolio_item_id == portfolio_item.id
    assert svc.imported_service_plan.service_offering_ref == str(
        service_offering.id
    )
    assert svc.imported_service_plan.schema["schemaType"] == "emptySchema"
    assert svc.imported_service_plan.imported is True


@pytest.mark.django_db
def test_import_service_plans_with_already_imported():
    service_offering = ServiceOfferingFactory()
    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )
    service_plan = CatalogServicePlanFactory(
        portfolio_item=portfolio_item,
    )

    with pytest.raises(ServicePlanImportedException) as excinfo:
        ImportServicePlan(portfolio_item).process()

    assert "Service plan was already imported" in str(excinfo.value)


@pytest.mark.django_db
def test_import_service_plans_with_empty_entities():
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )
    svc = ImportServicePlan(portfolio_item)
    svc.process()

    assert svc.imported_service_plan is None
