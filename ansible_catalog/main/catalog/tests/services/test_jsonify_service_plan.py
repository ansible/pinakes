"""Test the service of jsonify_service_plan"""
import pytest
import json

from ansible_catalog.main.catalog.tests.factories import (
    ServicePlanFactory,
    PortfolioItemFactory,
)

from ansible_catalog.main.catalog.services.jsonify_service_plan import (
    JsonifyServicePlan,
)

from ansible_catalog.main.inventory.tests.factories import (
    ServiceOfferingFactory,
)


@pytest.mark.django_db
def test_jsonify_service_plan_for_base():
    schema = {
        "schema": {
            "title": "",
            "fields": [
                {
                    "name": "sleep",
                    "type": "number",
                    "label": "Sleep Time (in seconds)",
                    "dataType": "integer",
                    "validate": [
                        {"type": "required-validator"},
                        {"type": "min-number-value", "value": 1},
                        {"type": "max-number-value", "value": 1800},
                    ],
                    "component": "text-field",
                    "helperText": "",
                    "isRequired": True,
                    "initialValue": 3,
                }
            ],
            "description": "",
        },
        "schemaType": "default",
    }
    service_offering = ServiceOfferingFactory()
    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )
    service_plan = ServicePlanFactory(
        portfolio_item=portfolio_item,
        base=schema,
    )

    # Test base
    options = {"schema": "base", "service_plan_id": service_plan.id}

    svc = JsonifyServicePlan(options)
    svc.process()

    assert svc.json[0]["name"] == service_plan.name
    assert svc.json[0]["description"] == service_plan.description
    assert svc.json[0]["portfolio_item_id"] == portfolio_item.id
    assert svc.json[0]["service_offering_id"] == str(service_offering.id)
    assert svc.json[0]["create_json_schema"] == schema
    assert svc.json[0]["modified"] is False
    assert svc.json[0]["imported"] is True

    # Test empty modified
    options = {"schema": "modified", "service_plan_id": service_plan.id}

    svc = JsonifyServicePlan(options)
    svc.process()

    assert svc.json[0]["name"] == service_plan.name
    assert svc.json[0]["description"] == service_plan.description
    assert svc.json[0]["portfolio_item_id"] == portfolio_item.id
    assert svc.json[0]["service_offering_id"] == str(service_offering.id)
    assert svc.json[0]["create_json_schema"] is None
    assert svc.json[0]["modified"] is False
    assert svc.json[0]["imported"] is True

    # Test modified
    service_plan = ServicePlanFactory(
        portfolio_item=portfolio_item,
        modified=schema,
    )

    options = {"schema": "modified", "service_plan_id": service_plan.id}

    svc = JsonifyServicePlan(options)
    svc.process()

    assert svc.json[0]["name"] == service_plan.name
    assert svc.json[0]["description"] == service_plan.description
    assert svc.json[0]["portfolio_item_id"] == portfolio_item.id
    assert svc.json[0]["service_offering_id"] == str(service_offering.id)
    assert svc.json[0]["create_json_schema"] == schema
    assert svc.json[0]["modified"] is True
    assert svc.json[0]["imported"] is True
