"""Start processing the next order item"""
import logging
from django.utils.translation import gettext_noop

from pinakes.main.catalog.models import OrderItem, ProgressMessage, ServicePlan
from pinakes.main.catalog.services.compute_runtime_parameters import (
    ComputeRuntimeParameters,
)
from pinakes.main.catalog.services.sanitize_parameters import (
    SanitizeParameters,
)
from pinakes.main.catalog.services.finish_order import (
    FinishOrder,
)
from pinakes.main.catalog.services.finish_order_item import (
    FinishOrderItem,
)
from pinakes.main.catalog.services.provision_order_item import (
    ProvisionOrderItem,
)
from pinakes.main.catalog.services.validate_order_item import (
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

            message = gettext_noop(
                "Submitting Order Item %(item_id)s for provisioning"
            )
            params = {"item_id": str(item.id)}

            item.update_message(ProgressMessage.Level.INFO, message, params)

            ValidateOrderItem(item).process()

            svc = ComputeRuntimeParameters(item).process()
            if svc.substituted:
                service_plan = ServicePlan.objects.get(
                    inventory_service_plan_ref=item.inventory_service_plan_ref
                )
                item.service_parameters = (
                    SanitizeParameters(service_plan, svc.runtime_parameters)
                    .process()
                    .sanitized_parameters
                )
                if item.service_parameters != svc.runtime_parameters:
                    item.service_parameters_raw = svc.runtime_parameters
                item.save()

            ProvisionOrderItem(item).process()

            logger.info(
                "OrderItem %d ordered with inventory task ref %s",
                item.id,
                item.inventory_task_ref,
            )
        except Exception as error:
            logger.error("Error Submitting Order Item: %s", str(error))

            FinishOrderItem(order_item=item, error_msg=str(error)).process()
