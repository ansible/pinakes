"""Sanitize the service parameters for a given order item"""

import logging
import re

from ansible_catalog.main.catalog.models import ServicePlan

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
        if (
            self.order_item.inventory_service_plan_ref is None
            or self.order_item.service_parameters is None
        ):
            return {}

        fields = self._service_plan_fields()
        service_parameters = self.order_item.service_parameters

        dicts = {
            field["name"]: self.MASKED_VALUE
            if self._mask_value(field)
            else service_parameters.get(field["name"])
            for field in fields
        }

        return {
            key: dicts.get(key) if dicts.get(key) else value
            for key, value in service_parameters.items()
        }

    def _service_plan_fields(self):
        service_plan = ServicePlan.objects.get(
            portfolio_item_id=self.order_item.portfolio_item.id
        )

        if (
            not service_plan.schema
            or service_plan.schema.get("schemaType") == "emptySchema"
        ):
            return []

        return service_plan.schema.get("schema", {}).get("fields", [])

    def _mask_value(self, field):
        need_mask = False

        for param in self.FILTERED_PARAMS:
            type = field.get("type", None)
            is_password = True if type == "password" else False
            need_mask = (
                need_mask
                or is_password
                or re.match(param, field.get("name"))
                or re.match(param, field.get("label"))
            )

        return need_mask
