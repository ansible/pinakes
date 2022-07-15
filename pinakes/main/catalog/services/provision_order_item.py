"""Start provisioning a Single order item"""
from django.utils.translation import gettext_noop

from pinakes.main.inventory.services.start_tower_job import (
    StartTowerJob,
)


class ProvisionOrderItem:
    """Start provisioning a single order item"""

    def __init__(self, order_item):
        self.order_item = order_item

    def process(self):
        """Process a single order item"""
        portfolio_item = self.order_item.portfolio_item
        params = {}
        params["service_parameters"] = (
            self.order_item.service_parameters_raw
            or self.order_item.service_parameters
        )
        params["service_plan_id"] = None

        svc = StartTowerJob(
            portfolio_item.service_offering_ref, params
        ).process()
        job = svc.job

        message = gettext_noop("Order Item %(id)s is provisioned")
        params = {"id": str(self.order_item.id)}
        self.order_item.mark_ordered(
            message=message,
            params=params,
            inventory_task_ref=job.id,
        )

        return self
