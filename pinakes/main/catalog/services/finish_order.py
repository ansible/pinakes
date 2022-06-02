"""Finish an order with correct state and status"""

import logging
from django.utils.translation import gettext_noop

from pinakes.main.catalog.models import (
    ApprovalRequest,
    OrderItem,
)

logger = logging.getLogger("catalog")


class FinishOrder:
    """Finish an order with correct state and status"""

    def __init__(self, order):
        self.order = order

    def process(self, is_complete=True):
        # clear sensitive data
        for item in self.order.order_items:
            item.service_parameters_raw = None
            item.save()

        # All order items are done
        if is_complete:
            if OrderItem.State.FAILED in [
                item.state for item in self.order.order_items
            ]:
                message = gettext_noop("Order %(order_id)s has failed")
                params = {"order_id": str(self.order.id)}
                self.order.mark_failed(message, params)
                logger.error("Order %d has failed", self.order.id)
            else:
                message = gettext_noop("Order %(order_id)s is completed")
                params = {"order_id": str(self.order.id)}
                self.order.mark_completed(message, params)
                logger.info("Order %d is completed", self.order.id)

            return self

        if self.order.approvalrequest.state == ApprovalRequest.State.CANCELED:
            self.order.mark_failed(gettext_noop("Order Canceled"))
        # For both ApprovalRequest.State.DENIED
        #   and ApprovalRequest.State.FAILED
        else:
            self.order.mark_failed(gettext_noop("Order Failed"))

        for item in self.order.order_items:
            if item.state not in OrderItem.FINISHED_STATES:
                message = gettext_noop(
                    "This order item has failed due to the entire \
order %(state)s before it ran"
                )
                params = {"state": self.order.approvalrequest.state}
                item.mark_failed(message, params)

        return self
