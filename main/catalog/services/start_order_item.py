""" Start Ordering a Single order item """

from main.inventory.services.start_tower_job import StartTowerJob
from main.catalog.models import OrderItem


class StartOrderItem:
    """Start handling a single order item"""

    def __init__(self, order_item):
        self.order_item = order_item

    def process(self):
        """Process a single order item"""
        portfolio_item = self.order_item.portfolio_item
        params = {}
        params["service_parameters"] = self.order_item.service_parameters
        params["service_plan_id"] = None

        job_id = StartTowerJob(
            portfolio_item.service_offering_ref, params
        ).process()
        self.order_item.state = OrderItem.State.ORDERED
        self.order_item.inventory_task_ref = job_id
        self.order_item.save()
        return self
