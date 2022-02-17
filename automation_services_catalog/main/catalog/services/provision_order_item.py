""" Start provisioning a Single order item """

from automation_services_catalog.main.inventory.services.start_tower_job import (
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
        params["service_parameters"] = self.order_item.service_parameters
        params["service_plan_id"] = None

        svc = StartTowerJob(
            portfolio_item.service_offering_ref, params
        ).process()
        job = svc.job

        self.order_item.mark_ordered(
            f"Order Item {self.order_item.id} is provisioned",
            inventory_task_ref=job.id,
        )

        return self
