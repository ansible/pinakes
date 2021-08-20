""" Start processing the next order item """
import logging

from main.catalog.models import Order, OrderItem, ProgressMessage
from main.catalog.services.finish_order import FinishOrder
from main.catalog.services.provision_order_item import ProvisionOrderItem

logger = logging.getLogger("catalog")


class StartOrderItem:
    """Start processing the next order item"""

    def __init__(self, order):
        self.order = order

    def process(self):
        items = [
            item
            for item in self.order.order_items
            if item.state not in OrderItem.FINISHED_STATES
        ]

        # All order items are processed
        if len(items) == 0:
            FinishOrder(self.order).process()
            return

        # Always start from the first
        item = items[0]

        try:
            logger.info(
                "Submitting Order Item {} for provisioning".format(item.id)
            )

            item.update_message(
                ProgressMessage.Level.INFO,
                "Submitting Order Item {} for provisioning".format(item.id),
            )

            self.__validate_before_provision()
            ProvisionOrderItem(item).process()

            logger.info(
                "OrderItem {} ordered with inventory task ref {}".format(
                    item.id, item.inventory_task_ref
                )
            )
        except Exception as error:
            item.mark_failed(
                "Error Submitting Order Item: {}".format(str(error))
            )
            logger.error("Error Submitting Order Item: {}".format(str(error)))

            # continue to process next order item if order is approved
            if self.order.state == Order.State.ORDERED:
                StartOrderItem(self.order).process()
            else:
                for item in self.order.order_items:
                    if item.state not in OrderItem.FINISHED_STATES:
                        item.mark_failed(
                            "This order item has failed due to the entire order failing before it ran"
                        )

                self.order.mark_failed(str(error))

        # TODO: compute runtime parameters later

    def __validate_before_provision(self):
        # TODO:
        pass
