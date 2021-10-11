"""Import the service plan"""

import logging
from django.utils.translation import gettext_lazy as _

from ansible_catalog.main.catalog.models import CatalogServicePlan
from ansible_catalog.main.catalog.services.fetch_service_plans import (
    FetchServicePlans,
)
from ansible_catalog.main.catalog.services.jsonify_service_plan import (
    JsonifyServicePlan,
)

logger = logging.getLogger("catalog")


class ImportServicePlan:
    """Import catalog service plan"""

    def __init__(self, portfolio_item, force_reset=False):
        self.portfolio_item = portfolio_item
        self.reimported_service_plan = None
        if force_reset:
            self._clear_service_plans()
        else:
            self._check_conflicts()

    def process(self):
        svc = FetchServicePlans(self.portfolio_item)
        svc._get_remote_service_plans()

        if len(svc.service_plans) == 0:
            logger.info(
                "There is no remote service plans for portfolio_item: %d",
                self.portfolio_item.id,
            )
            return self

        service_plan = svc.service_plans[0]
        CatalogServicePlan.objects.create(
            name=service_plan.name,
            portfolio_item=self.portfolio_item,
            base_schema=service_plan.base_schema,
            modified_schema=service_plan.modified_schema,
            create_json_schema=service_plan.create_json_schema,
            service_offering_ref=service_plan.service_offering_ref,
            service_plan_ref=service_plan.service_plan_ref,
            tenant=self.portfolio_item.tenant,
        )

        svc = JsonifyServicePlan(service_plan, {}).process()
        self.reimported_service_plan = svc.json

        return self

    def _clear_service_plans(self):
        service_plans = CatalogServicePlan.objects.filter(
            portfolio_item=self.portfolio_item
        )
        service_plans.delete()

    def _check_conflicts(self):
        service_plans = CatalogServicePlan.objects.filter(
            portfolio_item=self.portfolio_item
        )

        if len(service_plans) > 0:
            raise RuntimeError(
                _("Service Plan already exists for PortfolioItem: {}").format(
                    self.portfolio_item.id
                )
            )
