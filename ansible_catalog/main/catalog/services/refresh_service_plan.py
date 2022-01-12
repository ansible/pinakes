"""Refresh service plan from inventory"""

import logging

from ansible_catalog.main.catalog.models import ServicePlan
from ansible_catalog.main.catalog.utils import (
    compare_schema,
)
from ansible_catalog.main.inventory.services.get_service_offering import (
    GetServiceOffering,
)

logger = logging.getLogger("catalog")

EMPTY_SCHEMA = {
    "schemaType": "emptySchema",
    "schema": {
        "fields": [
            {
                "component": "plain-text",
                "name": "empty-service-plan",
                "label": "This product requires no user input and is fully configured by the system.\nClick submit to order this item.",
            }
        ]
    },
}
EMPTY_SHA256 = (
    "d6ac89987a40f596ee85e25d4c80f12b697370f92d4ec3a1a258c4dbf921cf8c"
)


class RefreshServicePlan:
    """
    Update base schema for a non-modified service plan.
    Compare base schemas for a modified service plan and flag the differences.
    """

    def __init__(self, service_plan):
        self.service_plan = service_plan

    def process(self):
        temp_service_plan = self._get_remote_schema()
        self.service_plan.name = temp_service_plan.name
        self.service_plan.inventory_service_plan_ref = (
            temp_service_plan.inventory_service_plan_ref
        )

        if (
            self.service_plan.modified
            and not self.service_plan.base_sha256
            == temp_service_plan.base_sha256
        ):
            changed_content = compare_schema(
                self.service_plan.base_schema, temp_service_plan.base_schema
            )
            logger.info(
                "Service plan %s changed with content: %s",
                self.service_plan.name,
                changed_content,
            )

            self.service_plan.outdated = True
            self.service_plan.outdated_changes = changed_content
        else:
            self.service_plan.base_schema = temp_service_plan.base_schema
            self.service_plan.base_sha256 = temp_service_plan.base_sha256
            self.service_plan.outdated = False
            self.service_plan.outdated_changes = ""

        self.service_plan.save()

        return self

    def _get_remote_schema(self):
        service_offering_ref = self.service_plan.service_offering_ref

        try:
            logger.info(
                "Fetching service plans from inventory: %s",
                service_offering_ref,
            )
            svc = GetServiceOffering(service_offering_ref, True).process()
        except Exception as error:
            logger.error("Error fetching service plans: %s", str(error))
            raise

        service_offering = svc.service_offering

        if service_offering and service_offering.survey_enabled:
            remote_service_plan = (
                svc.service_plans.first()
            )  # only choose the 1st one

            if remote_service_plan is None:
                logger.error(
                    "Service offering: %d has no service plans",
                    service_offering.id,
                )
                return ServicePlan(
                    name="",
                    inventory_service_plan_ref="",
                    base_sha256="",
                    base_schema=None,
                )
            else:
                return ServicePlan(
                    name=remote_service_plan.name,
                    inventory_service_plan_ref=str(remote_service_plan.id),
                    base_sha256=remote_service_plan.schema_sha256,
                    base_schema=remote_service_plan.create_json_schema,
                )
        else:
            return ServicePlan(
                name="",
                inventory_service_plan_ref="",
                base_sha256=EMPTY_SHA256,
                base_schema=EMPTY_SCHEMA,
            )
