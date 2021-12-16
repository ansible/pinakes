""" Test population json template with input parameters """
import pytest

from ansible_catalog.main.catalog.exceptions import (
    InvalidSurveyException,
)
from ansible_catalog.main.catalog.tests.factories import (
    OrderItemFactory,
    PortfolioItemFactory,
    ServicePlanFactory,
)
from ansible_catalog.main.inventory.tests.factories import (
    ServiceOfferingFactory,
    InventoryServicePlanFactory,
)
from ansible_catalog.main.catalog.services.validate_order_item import (
    ValidateOrderItem,
)


def schema1():
    schema = {
        "schemaType": "default",
        "schema": {
            "fields": [
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
                }
            ],
            "title": "",
            "description": "",
        },
    }

    return schema


def schema2():
    schema = {
        "schemaType": "default",
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

    return schema


@pytest.mark.django_db
def test_process_with_valid_order_item():
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )

    InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=schema1(),
    )
    ServicePlanFactory(portfolio_item=portfolio_item, base_schema=schema1())

    order_item = OrderItemFactory(portfolio_item=portfolio_item)

    svc = ValidateOrderItem(order_item)
    svc.process()

    assert svc.order_item == order_item


@pytest.mark.django_db
def test_process_with_invalid_order_item():
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )

    InventoryServicePlanFactory(
        service_offering=service_offering,
        create_json_schema=schema1(),
        schema_sha256="schema1",
    )
    ServicePlanFactory(
        portfolio_item=portfolio_item,
        base_schema=schema2(),
        base_sha256="schema2",
        modified_schema="schema2",
    )

    order_item = OrderItemFactory(portfolio_item=portfolio_item)

    svc = ValidateOrderItem(order_item)

    with pytest.raises(InvalidSurveyException) as excinfo:
        svc.process()

    assert "The underlying survey on" in str(excinfo.value)
