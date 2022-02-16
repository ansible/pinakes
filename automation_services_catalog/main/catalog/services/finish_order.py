"""Finish an order with correct state and status"""

import logging
from django.utils.translation import gettext_lazy as _

from automation_services_catalog.main.catalog.models import (
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
                self.order.mark_failed(
                    _("Order {} is failed".format(self.order.id))
                )
                logger.error("Order %d failed", self.order.id)
            else:
                self.order.mark_completed(
                    _("Order {} is completed".format(self.order.id))
                )
                logger.info("Order %d is completed", self.order.id)

            return self

        if self.order.approvalrequest.state == ApprovalRequest.State.CANCELED:
            self.order.mark_failed("Order Canceled")
        # for both ApprovalRequest.State.DENIED and  ApprovalRequest.State.FAILED
        else:
            self.order.mark_failed("Order Failed")

        for item in self.order.order_items:
            if item.state not in OrderItem.FINISHED_STATES:
                item.mark_failed(
                    _(
                        "This order item has failed due to the entire order {} before it ran".format(
                            self.order.approvalrequest.state
                        )
                    )
                )

        return self
