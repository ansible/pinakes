"""Sanitize the service parameters for a given order item"""

import logging
import re

from ansible_catalog.main.catalog.models import ServicePlan
from ansible_catalog.main.inventory.services.get_service_plan import (
    GetServicePlan,
)

logger = logging.getLogger("catalog")


class SanitizeParameters:
    """Sanitize the parameters for a given order item"""

    MASKED_VALUE = "$protected$"
    FILTERED_PARAMS = ["password", "token", "secret"]

    def __init__(self, order_item):
        self.order_item = order_item
        self.sanitized_parameters = {}

    def process(self):
        try:
            logger.info("Santizing service parameters ...")
            self.sanitized_parameters = self._compute_sanitized_parameters()

            return self
        except Exception as exc:
            logger.error(
                "Failed to sanitize parameters for order item %d, error: %s",
                self.order_item.id,
                str(exc),
            )
            raise

    def _compute_sanitized_parameters(self):
        if self.order_item.inventory_service_plan_ref is None:
            return {}

        fields = self._service_plan_fields()
        service_parameters = self.order_item.service_parameters

        dicts = {}
        for field in fields:
            dicts[field["name"]] = (
                self.MASKED_VALUE
                if self._mask_value(field)
                else service_parameters[field["name"]]
            )

        result = {}

        for key, __value in service_parameters.items():
            result[key] = dicts[key]

        return result

    def _service_plan_fields(self):
        service_plan = ServicePlan.objects.filter(
            portfolio_item_id=self.order_item.portfolio_item.id
        ).first()

        if service_plan is None:
            service_plan_schema = (
                GetServicePlan(self.order_item.inventory_service_plan_ref)
                .proces()
                .service_plan.create_json_schema
            )
        else:
            service_plan_schema = (
                service_plan.schema
                or GetServicePlan(self.order_item.inventory_service_plan_ref)
                .proces()
                .service_plan.create_json_schema
            )

        return service_plan_schema["schema"]["fields"]

    def _mask_value(self, field):
        need_mask = False

        for param in self.FILTERED_PARAMS:
            type = field.get("type", None)
            is_password = False if type is None else type == "password"
            need_mask = (
                need_mask
                or is_password
                or re.match(param, field["name"])
                or re.match(param, field["label"])
            )

        return need_mask
