""" Module to Finish Processing an OrderItem """
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from main.catalog.models import OrderItem, ProgressMessage


class FinishOrderItem:
    """Finish an OrderItem"""

    def __init__(self, task_id, artifacts, error_msg=None):
        self.order_item = OrderItem.objects.filter(
            inventory_task_ref=task_id
        ).first()
        self.error_msg = error_msg
        self.artifacts = artifacts

    def process(self):
        from main.catalog.services.start_order_item import StartOrderItem

        """Finish processing the order_item"""
        if self.error_msg is None:
            self.order_item.mark_completed(
                _("Order Item {} is completed").format(self.order_item.id),
                artifacts=self.artifacts,
            )
        else:
            self.order_item.mark_failed(self.error_msg)

        StartOrderItem(self.order_item.order).process()

        return self
