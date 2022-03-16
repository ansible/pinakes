"""Sanitize the service parameters for a given order item"""

import logging
import re
from django.utils.translation import gettext_lazy as _

from pinakes.main.catalog.exceptions import BadParamsException

logger = logging.getLogger("catalog")


class SanitizeParameters:
    """Sanitize the parameters for a given order item"""

    MASKED_VALUE = "$protected$"
    FILTERED_PARAMS = ["password", "token", "secret"]

    def __init__(self, service_plan, service_parameters):
        self.service_parameters = service_parameters
        self.sanitized_parameters = {}
        self.fields = service_plan.schema.get("schema", {}).get("fields", [])

    def process(self):
        logger.info("Sanitizing service parameters ...")
        self._validate_parameters()
        self._compute_sanitized_parameters()

        return self

    def _validate_parameters(self):
        for field in self.fields:
            name = field["name"]
            present = name in self.service_parameters
            present_but_empty = (
                present and self.service_parameters[name] is None
            )
            required = field.get("isRequired", False)
            if not required and present_but_empty:
                del self.service_parameters[name]
            elif required and (not present or present_but_empty):
                raise BadParamsException(
                    _("parameter {} is required and must have a value").format(
                        name
                    )
                )

    def _compute_sanitized_parameters(self):
        dicts = {
            field["name"]: self.MASKED_VALUE
            if self._mask_value(field)
            else self.service_parameters.get(field["name"])
            for field in self.fields
        }

        self.sanitized_parameters = {
            key: dicts.get(key) if dicts.get(key) else value
            for key, value in self.service_parameters.items()
        }

    def _mask_value(self, field):
        need_mask = False

        for param in self.FILTERED_PARAMS:
            is_password = field.get("type") == "password"
            need_mask = (
                need_mask
                or is_password
                or re.match(param, field.get("name"))
                or re.match(param, field.get("label"))
            )

        return need_mask
