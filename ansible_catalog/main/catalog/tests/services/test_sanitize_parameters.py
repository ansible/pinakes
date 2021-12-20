"""Test sanitize order item's parameters"""
import pytest

from ansible_catalog.main.catalog.services.sanitize_parameters import (
    SanitizeParameters,
)
from ansible_catalog.main.catalog.tests.factories import (
    OrderItemFactory,
    PortfolioItemFactory,
    make_service_plan,
)


@pytest.mark.django_db
def test_sanitize_parameters_from_service_plan_base():
    fields = [
        {
            "name": "Totally not a pass",
            "type": "password",
            "label": "Totally not a pass",
            "component": "text-field",
            "helperText": "",
            "isRequired": True,
            "initialValue": "",
        },
        {
            "name": "most_important_var1",
            "label": "secret field 1",
            "component": "textarea-field",
            "helperText": "Has no effect on anything, ever.",
            "initialValue": "",
        },
        {
            "name": "token idea",
            "label": "field 1",
            "component": "textarea-field",
            "helperText": "Don't look.",
            "initialValue": "",
        },
        {
            "name": "name",
            "label": "field 1",
            "component": "textarea-field",
            "helperText": "That's not my name.",
            "initialValue": "{{product.artifacts.testk}}",
            "isSubstitution": True,
        },
    ]

    base = {"schema": {"fields": fields}}
    service_parameters = {
        "name": "Joe",
        "Totally not a pass": "s3crete",
        "token idea": "my secret",
    }

    service_plan = make_service_plan(base)
    order_item = OrderItemFactory(
        portfolio_item=service_plan.portfolio_item,
        service_parameters=service_parameters,
        inventory_service_plan_ref=str(service_plan.id),
    )

    svc = SanitizeParameters(order_item).process()
    assert svc.sanitized_parameters == {
        "name": "Joe",
        "Totally not a pass": "$protected$",
        "token idea": "$protected$",
    }
