""" Cancel an order request"""
import logging

from django.utils.translation import gettext_lazy as _

from pinakes.main.approval.models import Action
from pinakes.main.approval.services.create_action import (
    CreateAction,
)
from pinakes.main.catalog.exceptions import (
    UncancelableException,
)
from pinakes.main.catalog.models import ApprovalRequest, Order

logger = logging.getLogger("catalog")


class CancelOrder:
    """Cancel an order request"""

    UNCANCELLABLE_STATES = [
        Order.State.COMPLETED,
        Order.State.FAILED,
        Order.State.ORDERED,
    ]

    def __init__(self, order):
        self.order = order

    def process(self):
        if self.order.state in self.UNCANCELLABLE_STATES:
            self._raise_uncancellable_error()

        try:
            approval_requests = ApprovalRequest.objects.filter(
                order=self.order
            )
            for request in approval_requests:
                CreateAction(
                    request.approval_request_ref,
                    {
                        "operation": Action.Operation.CANCEL,
                        "comments": f"Order {self.order.id} canceled",
                    },
                ).process()

            self.order.state = Order.State.CANCELED
            self.order.save()
            self.order.refresh_from_db()

        except Exception as error:
            logger.error(
                "Failed to cancel order %d, error: %s", self.order.id, error
            )
            self._raise_uncancellable_error()

        return self

    def _raise_uncancellable_error(self):
        error_message = _(
            "Order {} is not cancelable in its current state: {}"
        ).format(self.order.id, self.order.state)
        logger.error(error_message)

        raise UncancelableException(error_message)
