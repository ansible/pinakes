""" Fetch latest service plans from inventory. """

import logging

from ansible_catalog.main.catalog.models import CatalogServicePlan
from ansible_catalog.main.inventory.services.get_service_offering import (
    GetServiceOffering,
)

logger = logging.getLogger("catalog")


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

            if service_plans.count() == 0:
                self.get_remote_service_plans()
            else:
                self._get_local_service_plans(service_plans)

            return self
        except Exception as error:
            logger.error("Error fetching service plans: %s", str(error))
            raise

    def _get_local_service_plans(self, service_plans):
        for service_plan in service_plans:
            service_plan.name = service_plan.name
            service_plan.portfolio_item = self.portfolio_item
            service_plan.service_offering_ref = (
                self.portfolio_item.service_offering_ref
            )
            service_plan.create_json_schema = (
                service_plan.modified_schema or service_plan.base_schema or {}
            )
            service_plan.service_plan_ref = service_plan.service_plan_ref

            self.service_plans.append(service_plan)

    def get_remote_service_plans(self):
        service_offering_ref = self.portfolio_item.service_offering_ref
        svc = GetServiceOffering(service_offering_ref, True).process()

        service_offering = svc.service_offering

        if service_offering and service_offering.survey_enabled:
            service_plan = svc.service_plans.first()  # only choose the 1st one

            if service_plan is None:
                logger.error(
                    "Service offering: %d has no service plans",
                    service_offering.id,
                )
                self.service_plans = []
                return

            catalog_service_plan = CatalogServicePlan(
                id=service_plan.id,
                name=service_plan.name,
                portfolio_item=self.portfolio_item,
                service_offering_ref=service_offering.id,
                service_plan_ref=str(service_plan.id),
                create_json_schema=service_plan.create_json_schema or {},
                imported=False,
            )
        else:
            catalog_service_plan = CatalogServicePlan(
                portfolio_item=self.portfolio_item,
                service_offering_ref=service_offering.id,
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
                imported=False,
            )

        self.service_plans = [catalog_service_plan]
