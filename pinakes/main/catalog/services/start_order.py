"""Approval Request State Transition"""

import logging
from django.utils.translation import gettext_lazy as _

from pinakes.main.catalog.services.start_order_item import (
    StartOrderItem,
)

logger = logging.getLogger("catalog")


class StartOrder:
    """Start the order"""

    def __init__(self, order):
        self.order = order

    def process(self):
        logger.info("Submitting Order for provisioning...")
        self.order.mark_ordered(_("Submitting Order for provisioning"))

        StartOrderItem(self.order).process()
        return self
