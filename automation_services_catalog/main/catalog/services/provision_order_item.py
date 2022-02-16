""" Start provisioning a Single order item """
import logging
from django.utils.translation import gettext_lazy as _

from automation_services_catalog.main.catalog.exceptions import (
    BadProvisionException,
)
from automation_services_catalog.main.inventory.services.start_tower_job import (
    StartTowerJob,
)

logger = logging.getLogger("catalog")


class ProvisionOrderItem:
    """Start provisioning a single order item"""

    def __init__(self, order_item):
        self.order_item = order_item

    def process(self):
        """Process a single order item"""
        portfolio_item = self.order_item.portfolio_item
        params = {}
        params["service_parameters"] = self.order_item.service_parameters
        params["service_plan_id"] = None

        try:
            svc = StartTowerJob(
                portfolio_item.service_offering_ref, params
            ).process()
            job = svc.job

            self.order_item.mark_ordered(
                f"Order Item {self.order_item.id} is provisioned",
                inventory_task_ref=job.id,
            )

            return self
        except Exception as error:
            logger.error(
                "Error provisioning order item %s: %s",
                self.order_item.name,
                str(error),
            )

            raise BadProvisionException(
                _("Failed to provision order item {}").format(
                    self.order_item.name
                )
            ) from error
