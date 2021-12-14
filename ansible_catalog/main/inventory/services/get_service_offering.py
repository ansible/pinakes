""" Get service plan for a given service plan id """

from django.utils.translation import gettext_lazy as _
from ansible_catalog.main.inventory.models import (
    InventoryServicePlan,
    ServiceOffering,
)

from ansible_catalog.main.catalog.exceptions import (
    BadParamsException,
)


class GetServiceOffering:
    """Get service plan for a given service plan id"""

    def __init__(self, service_offering_id, get_service_plans=False):
        try:
            self.service_offering = ServiceOffering.objects.filter(
                id=int(service_offering_id)
            ).first()
            if get_service_plans:
                self.service_plans = InventoryServicePlan.objects.filter(
                    service_offering=self.service_offering
                )
        except Exception:
            raise BadParamsException(
                _("Failed to get service offering [{}]").format(
                    service_offering_id
                )
            )

    def process(self):
        return self
