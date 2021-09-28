""" Fetch latest service plans from inventory. """

import logging
import json

from ansible_catalog.main.catalog.models import CatalogServicePlan
from ansible_catalog.main.inventory.services.get_service_offering import (
    GetServiceOffering,
)

logger = logging.getLogger("catalog")


class ServicePlanTemplate:
    """Template for service plans"""

    def __init__(
        self,
        portfolio_item_id,
        service_offering_id,
        create_json_schema,
        id=None,
        name="",
        description="",
        imported=False,
        modified=False,
    ):
        self.portfolio_item_id = portfolio_item_id
        self.service_offering_id = service_offering_id
        self.create_json_schema = create_json_schema
        self.id = id
        self.name = name
        self.description = description
        self.imported = imported
        self.modified = modified


class FetchServicePlans:
    """Fetch latest service plans from inventory"""

    def __init__(self, portfolio_item):
        self.portfolio_item = portfolio_item
        self.service_plans = []

    def process(self):
        try:
            service_plans = CatalogServicePlan.objects.filter(
                portfolio_item=self.portfolio_item
            )

            if len(service_plans) == 0:
                self._get_remote_service_plans()
            else:
                self._get_local_service_plans(service_plans)

            return self
        except Exception as error:
            logger.error("Error fetching service plans: %s", str(error))
            raise

    def _get_local_service_plans(self, service_plans):
        for service_plan in service_plans:
            service_plan_template = ServicePlanTemplate(
                portfolio_item_id=self.portfolio_item.id,
                service_offering_id=self.portfolio_item.service_offering_ref,
                create_json_schema=json.loads(
                    json.loads(
                        service_plan.modified or service_plan.base or '"{}"'
                    )
                ),
                id=service_plan.id,
                name=service_plan.name,
            )
            self.service_plans.append(service_plan_template.__dict__)

    def _get_remote_service_plans(self):
        service_offering_ref = self.portfolio_item.service_offering_ref
        svc = GetServiceOffering(service_offering_ref, True).process()

        service_offering = svc.service_offering

        if service_offering.survey_enabled:
            service_plan = svc.service_plans.first()  # only choose the 1st one

            service_plan_template = ServicePlanTemplate(
                portfolio_item_id=self.portfolio_item.id,
                service_offering_id=service_offering.id,
                create_json_schema=json.loads(
                    service_plan.create_json_schema or "{}"
                ),
                id=service_plan.id,
                name=service_plan.name,
            )
        else:
            service_plan_template = ServicePlanTemplate(
                portfolio_item_id=self.portfolio_item.id,
                service_offering_id=service_offering.id,
                create_json_schema={
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
                },
            )

        self.service_plans = [service_plan_template.__dict__]
