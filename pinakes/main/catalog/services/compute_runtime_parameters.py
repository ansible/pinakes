"""Compute service parameters in runtime"""
from pinakes.main.catalog.models import (
    ServicePlan,
)


class ComputeRuntimeParameters:
    """Start to compute service parameters in runtime"""

    def __init__(self, order_item):
        self.order_item = order_item
        self.runtime_parameters = {}

    def process(self):
        if self.order_item.inventory_service_plan_ref is None:
            return self

        service_parameters_raw = (
            self.order_item.service_parameters_raw
            or self.order_item.service_parameters
            or {}
        )

        field_names = [
            field.get("name") for field in self._fields() if field.get("name")
        ]

        self.runtime_parameters = {
            key: self._compute_value(key, value)
            for key, value in service_parameters_raw.items()
            if key in field_names
        }

        return self

    def _fields(self):
        # each portfolio_item must have one service plan
        service_plan = ServicePlan.objects.get(
            portfolio_item=self.order_item.portfolio_item
        )
        if (
            not service_plan.schema
            or service_plan.schema.get("schemaType") == "emptySchema"
        ):
            return []

        return service_plan.schema.get("schema", {}).get("fields", [])

    def _compute_value(self, key, value):
        for field in self._fields():
            if field.get("name") == key and not field.get("isSubstitution"):
                return value

        return self._substitution(value)

    # TODO:
    def _substitution(self, value):
        return value
