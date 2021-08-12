""" Module to Finish Processing an OrderItem """
from django.utils import timezone
from main.catalog.models import OrderItem


class FinishOrderItem:
    """Finish an OrderItem"""

    def __init__(self, task_id, artifacts, error_msg=None):
        self.order_item = OrderItem.objects.filter(
            inventory_task_ref=task_id
        ).first()
        self.error_msg = error_msg
        self.artifacts = artifacts

    def process(self):
        """Finish processing the order_item"""
        if self.error_msg is None:
            self.order_item.state = OrderItem.State.COMPLETED
            self.order_item.artifacts = self.artifacts
        else:
            self.order_item.state = OrderItem.State.FAILED

        self.order_item.completed_at = timezone.now()
        self.order_item.save()
        return self
