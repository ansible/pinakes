"""Test population json template with input parameters"""
import pytest

from pinakes.main.catalog.tests.factories import (
    OrderFactory,
    OrderItemFactory,
    PortfolioItemFactory,
    ServicePlanFactory,
)
from pinakes.main.catalog.services.compute_runtime_parameters import (
    ComputeRuntimeParameters,
)


def fields_1():
    fields = [
        {
            "component": "plain-text",
            "name": "empty-service-plan",
            "label": (
                "This product requires no user input and is fully configured"
                " by the system."
            ),
        }
    ]

    return fields


def fields_2():
    return [
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
        {
            "name": "flexible",
            "type": "string",
            "label": "flexible",
            "component": "textarea-field",
            "helperText": "",
            "initialValue": "{{product.artifacts.testk}}",
            "isSubstitution": True,
        },
    ]


def schema(fields):
    return {
        "schemaType": "default",
        "schema": {
            "fields": fields,
            "title": "",
            "description": "",
        },
    }


@pytest.mark.django_db
def test_process_without_service_plan_ref_in_order_item():
    portfolio_item = PortfolioItemFactory()
    ServicePlanFactory(
        portfolio_item=portfolio_item,
    )
    order_item = OrderItemFactory(
        portfolio_item=portfolio_item,
    )

    svc = ComputeRuntimeParameters(order_item)
    svc.process()

    assert svc.runtime_parameters == {}


@pytest.mark.django_db
def test_process_without_service_parameters_in_order_item():
    inventory_service_plan_id = 1
    portfolio_item = PortfolioItemFactory()
    ServicePlanFactory(
        base_schema=schema(fields_1()),
        inventory_service_plan_ref=str(inventory_service_plan_id),
        portfolio_item=portfolio_item,
    )
    order_item = OrderItemFactory(
        portfolio_item=portfolio_item,
        inventory_service_plan_ref=str(inventory_service_plan_id),
    )

    svc = ComputeRuntimeParameters(order_item)
    svc.process()

    assert svc.runtime_parameters == {}


@pytest.mark.django_db
def test_process_without_schema_in_service_plan():
    inventory_service_plan_id = 1
    portfolio_item = PortfolioItemFactory()
    ServicePlanFactory(
        base_schema=None,
        inventory_service_plan_ref=str(inventory_service_plan_id),
        portfolio_item=portfolio_item,
    )
    order_item = OrderItemFactory(
        portfolio_item=portfolio_item,
        inventory_service_plan_ref=str(inventory_service_plan_id),
    )

    svc = ComputeRuntimeParameters(order_item)
    svc.process()

    assert svc.runtime_parameters == {}


@pytest.mark.django_db
def test_process_with_schema_in_service_plan():
    inventory_service_plan_id = 1
    portfolio_item = PortfolioItemFactory()
    ServicePlanFactory(
        base_schema=schema(fields_1()),
        inventory_service_plan_ref=str(inventory_service_plan_id),
        portfolio_item=portfolio_item,
    )
    order_item = OrderItemFactory(
        portfolio_item=portfolio_item,
        inventory_service_plan_ref=str(inventory_service_plan_id),
        service_parameters={"extra": "not in schema fields"},
    )

    svc = ComputeRuntimeParameters(order_item)
    svc.process()

    assert svc.runtime_parameters == {}


@pytest.mark.django_db
def test_process_with_service_parameters_not_in_schema():
    inventory_service_plan_id = 1
    portfolio_item = PortfolioItemFactory()
    ServicePlanFactory(
        base_schema=schema(fields_1()),
        inventory_service_plan_ref=str(inventory_service_plan_id),
        portfolio_item=portfolio_item,
    )
    order_item = OrderItemFactory(
        portfolio_item=portfolio_item,
        inventory_service_plan_ref=str(inventory_service_plan_id),
        service_parameters={"extra": "not in schema fields"},
    )

    svc = ComputeRuntimeParameters(order_item)
    svc.process()

    assert svc.runtime_parameters == {}


@pytest.mark.django_db
def test_process_with_service_parameters_in_schema():
    inventory_service_plan_id = 1
    portfolio_item = PortfolioItemFactory()
    ServicePlanFactory(
        outdated=False,
        portfolio_item=portfolio_item,
        base_schema=schema(fields_2()),
        inventory_service_plan_ref=str(inventory_service_plan_id),
    )

    order = OrderFactory()
    order_item = OrderItemFactory(
        order=order,
        inventory_service_plan_ref=str(inventory_service_plan_id),
        service_parameters={
            "extra": "not in schema fields",
            "flexible": "in schema fields",
            "fixed": "fixed",
            "dev_null": "change in future",
        },
        portfolio_item=portfolio_item,
    )

    svc = ComputeRuntimeParameters(order_item)
    svc.process()

    assert svc.runtime_parameters == {
        "dev_null": "change in future",
        "flexible": "in schema fields",
    }
    assert svc.substituted is True
