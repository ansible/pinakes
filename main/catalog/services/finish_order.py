""" Approval Request State Transition """

import logging

from main.catalog.models import (
    ApprovalRequest,
    Order,
    OrderItem,
    ProgressMessage,
)

logger = logging.getLogger("catalog")


class FinishOrder:
    """Approval Request State Transition"""

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
                    "Order {} is failed".format(self.order.id)
                )
                logger.error("Order {} failed".format(self.order.id))
            else:
                self.order.mark_completed(
                    "Order {} is completed".format(self.order.id)
                )
                logger.info("Order {} is completed".format(self.order.id))

            return self

        if self.order.approvalrequest.state == ApprovalRequest.State.CANCELED:
            self.order.mark_failed("Order Canceled")
        # for both ApprovalRequest.State.DENIED and  ApprovalRequest.State.FAILED
        else:
            self.order.mark_failed("Order Failed")

        for item in self.order.order_items:
            if item.state not in OrderItem.FINISHED_STATES:
                item.mark_failed(
                    "This order item has failed due to the entire order {} before it ran".format(
                        self.order.approvalrequest.state
                    )
                )

        return self
