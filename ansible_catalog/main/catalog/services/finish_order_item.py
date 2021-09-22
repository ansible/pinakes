""" Module to Finish Processing an OrderItem """
import logging

from django.utils.translation import gettext_lazy as _
from ansible_catalog.main.catalog.models import OrderItem

logger = logging.getLogger("catalog")


class FinishOrderItem:
    """Finish an OrderItem"""

    def __init__(
        self,
        order_item=None,
        inventory_task_ref=None,
        artifacts={},
        error_msg=None,
    ):
        self.order_item = order_item or self._get_order_item(
            inventory_task_ref
        )
        self.error_msg = error_msg
        self.artifacts = artifacts

    def process(self):
        from ansible_catalog.main.catalog.services.start_order_item import (
            StartOrderItem,
        )

        if self.order_item is None:
            logger.warn("Order item is not available")
            return self

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

    def _get_order_item(self, inventory_task_ref):
        return OrderItem.objects.filter(
            inventory_task_ref=inventory_task_ref
        ).first()
