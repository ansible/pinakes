"""Refresh service plan from inventory"""

import logging

from ansible_catalog.main.catalog.models import CatalogServicePlan
from ansible_catalog.main.inventory.services.get_service_offering import (
    GetServiceOffering,
)

logger = logging.getLogger("catalog")

EMPTY_SCHEMA={
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

class RefreshServicePlan:
    """
    Update base schema for a non-modified service plan.
    Compare base schemas for a modified service plan and flag the differences.
    """

    def __init__(self, service_plan):
        self.service_plan = service_plan

    def process(self):
        remote_plan = self._get_remote_schema()
        self.service_plan.name = remote_plan[0]
        self.service_plan.service_plan_ref = remote_plan[1]
        remote_schema = remote_plan[2]
        if self.service_plan.modified and not remote_schema == self.service_plan.base_schema:
            self.service_plan.outdated = True
            # TODO: fill in the actual changes
            self.service_plan.outdated_changes = "Base schema from inventory has changed"
        else:
            self.service_plan.base_schema = remote_schema
            self.service_plan.outdated = False
            self.service_plan.outdated_changes = ""

        self.service_plan.save()

        return self

    def _get_remote_schema(self):
        """return (name, id, schema)"""
        service_offering_ref = self.service_plan.service_offering_ref

        try:
            logger.info("Fetching service plans from inventory: %s", service_offering_ref)
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
                return ("", "", None)
            else:
                return (remote_service_plan.name, str(remote_service_plan.id), remote_service_plan.create_json_schema)
        else:
            return ("", "", EMPTY_SCHEMA)
