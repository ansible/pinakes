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

    svc = JsonifyServicePlan(service_plan, options)
    svc.process()

    assert svc.json["name"] == service_plan.name
    assert svc.json["description"] == service_plan.description
    assert svc.json["portfolio_item_id"] == portfolio_item.id
    assert svc.json["service_offering_id"] == str(service_offering.id)
    assert svc.json["create_json_schema"] == schema
    assert svc.json["modified"] is False
    assert svc.json["imported"] is True

    # Test empty modified
    options = {"schema": "modified", "service_plan_id": service_plan.id}

    svc = JsonifyServicePlan(service_plan, options)
    svc.process()

    assert svc.json["name"] == service_plan.name
    assert svc.json["description"] == service_plan.description
    assert svc.json["portfolio_item_id"] == portfolio_item.id
    assert svc.json["service_offering_id"] == str(service_offering.id)
    assert svc.json["create_json_schema"] is None
    assert svc.json["modified"] is False
    assert svc.json["imported"] is True

    # Test modified
    service_plan = ServicePlanFactory(
        portfolio_item=portfolio_item,
        modified=schema,
    )

    options = {"schema": "modified", "service_plan_id": service_plan.id}

    svc = JsonifyServicePlan(service_plan, options)
    svc.process()

    assert svc.json["name"] == service_plan.name
    assert svc.json["description"] == service_plan.description
    assert svc.json["portfolio_item_id"] == portfolio_item.id
    assert svc.json["service_offering_id"] == str(service_offering.id)
    assert svc.json["create_json_schema"] == schema
    assert svc.json["modified"] is True
    assert svc.json["imported"] is True
