"""Module to Finish Processing an OrderItem"""
import logging

from django.utils.translation import gettext_noop
from pinakes.main.catalog.models import OrderItem

logger = logging.getLogger("catalog")


class FinishOrderItem:
    """Finish an OrderItem"""

    def __init__(self, **params):
        logger.info("FinishOrderItem input params: %s", params)

        self.inventory_task_ref = params.pop("inventory_task_ref", None)
        self.order_item = params.pop("order_item", self._get_order_item())
        self.error_msg = params.pop("error_msg", None)
        self.artifacts = params.pop("artifacts", None)
        self.external_url = params.pop("external_url", None)
        self.service_instance_ref = params.pop("service_instance_ref", None)

    def process(self):
        from pinakes.main.catalog.services.start_order_item import (
            StartOrderItem,
        )

        if self.order_item is None:
            logger.warning("Order item is not available")
            return self

        """Finish processing the order_item"""
        if self.error_msg is None:
            message = gettext_noop("Order Item %(id)s is completed")
            params = {"id": str(self.order_item.id)}

            self.order_item.mark_completed(
                message=message,
                params=params,
                artifacts=self.artifacts,
                external_url=self.external_url or "",
                service_instance_ref=self.service_instance_ref,
            )
        else:
            self.order_item.mark_failed(self.error_msg)

        StartOrderItem(self.order_item.order).process()

        return self

    def _get_order_item(self):
        return OrderItem.objects.filter(
            inventory_task_ref=self.inventory_task_ref
        ).first()
