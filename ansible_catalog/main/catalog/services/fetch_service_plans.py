""" Fetch latest service plans from inventory. """

from ansible_catalog.main.catalog.models import ServicePlan
from ansible_catalog.main.catalog.services.refresh_service_plan import (
    RefreshServicePlan,
)


class FetchServicePlans:
    """
    Fetch service plans for portfolio_item.
    Create service plans if not exits.
    Update base schema for existing non-modified service plans.
    Compare base schemas for modified service plans.
    """

    def __init__(self, portfolio_item):
        self.portfolio_item = portfolio_item
        self.service_plans = []

    def process(self):
        local_service_plans = ServicePlan.objects.filter(
            portfolio_item=self.portfolio_item
        )

        if local_service_plans.count() == 0:
            self.service_plans = self._create_service_plans()
        else:
            self.service_plans = local_service_plans.all()

        RefreshServicePlan(self.service_plans[0]).process()

        return self

    def _create_service_plans(self):
        service_offering_ref = self.portfolio_item.service_offering_ref

        service_plan = ServicePlan.objects.create(
            portfolio_item=self.portfolio_item,
            service_offering_ref=self.portfolio_item.service_offering_ref,
            tenant=self.portfolio_item.tenant,
        )

        return (service_plan,)
