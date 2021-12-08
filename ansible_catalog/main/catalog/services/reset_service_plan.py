"""Reset the service plan"""

import logging
from ansible_catalog.main.catalog.models import CatalogServicePlan
from ansible_catalog.main.catalog.services.import_service_plan import (
    FetchServicePlans,
)

logger = logging.getLogger("catalog")


class ResetServicePlan:
    """Reset catalog service plan"""

    def __init__(self, service_plan):
        self.service_plan = service_plan

    def process(self):
        self.service_plan.modified_schema = None

        portfolio_item = self.service_plan.portfolio_item
        svc = FetchServicePlans(portfolio_item, True).process()

        if len(svc.service_plans) == 0:
            logger.info(
                "There is no remote service plans for portfolio_item: %d",
                portfolio_item.id,
            )
            self.service_plan.base_schema = None
        else:
            imported_service_plan = svc.service_plans[0]
            self.service_plan.base_schema = imported_service_plan.base_schema

        self.service_plan.save()
        return self
