"""Import the service plan"""

import logging
from django.utils.translation import gettext_lazy as _

from ansible_catalog.main.catalog.models import CatalogServicePlan
from ansible_catalog.main.catalog.services.fetch_service_plans import (
    FetchServicePlans,
)
from ansible_catalog.main.catalog.exceptions import (
    ServicePlanImportedException,
)

logger = logging.getLogger("catalog")


class ImportServicePlan:
    """Import and save catalog service plans from remote inventory"""

    def __init__(self, portfolio_item):
        self.portfolio_item = portfolio_item
        self.imported_service_plan = None
        self._check_conflicts()

    def process(self):
        svc = FetchServicePlans(self.portfolio_item, force_remote=True)
        svc.process()

        if len(svc.service_plans) == 0:
            logger.info(
                "There is no remote service plans for portfolio_item: %d",
                self.portfolio_item.id,
            )
            return self

        self.imported_service_plan = svc.service_plans[0]
        self.imported_service_plan.tenant = self.portfolio_item.tenant
        self.imported_service_plan.save()

        return self

    def _check_conflicts(self):
        service_plans = CatalogServicePlan.objects.filter(
            portfolio_item=self.portfolio_item
        )

        if service_plans.count() > 0:
            raise ServicePlanImportedException(
                _(
                    "Service plan was already imported for PortfolioItem: {}"
                ).format(self.portfolio_item.id)
            )
