""" Start processing the next order item """
import logging
from django.utils.translation import gettext_lazy as _

from automation_services_catalog.main.catalog.models import (
    OrderItem,
    ProgressMessage,
)
from automation_services_catalog.main.catalog.services.compute_runtime_parameters import (
    ComputeRuntimeParameters,
)
from automation_services_catalog.main.catalog.services.finish_order import FinishOrder
from automation_services_catalog.main.catalog.services.finish_order_item import (
    FinishOrderItem,
)
from automation_services_catalog.main.catalog.services.provision_order_item import (
    ProvisionOrderItem,
)
from automation_services_catalog.main.catalog.services.validate_order_item import (
    ValidateOrderItem,
)

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
            logger.info("Submitting Order Item %d for provisioning", item.id)

            item.update_message(
                ProgressMessage.Level.INFO,
                _("Submitting Order Item {} for provisioning".format(item.id)),
            )

            ValidateOrderItem(item).process()
            ProvisionOrderItem(item).process()

            logger.info(
                "OrderItem %d ordered with inventory task ref %s",
                item.id,
                item.inventory_task_ref,
            )
        except Exception as error:
            logger.error("Error Submitting Order Item: %s", str(error))

            FinishOrderItem(order_item=item, error_msg=str(error)).process()
        finally:
            svc = ComputeRuntimeParameters(item).process()
            if bool(svc.runtime_parameters):
                item.service_parameters = svc.runtime_parameters
                item.save()
