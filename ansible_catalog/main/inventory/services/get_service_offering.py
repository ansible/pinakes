""" Get service plan for a given service plan id """

from ansible_catalog.main.inventory.models import ServiceOffering, ServicePlan


class GetServiceOffering:
    """Get service plan for a given service plan id"""

    def __init__(self, service_offering_id, get_service_plans=False):
        self.service_offering = ServiceOffering.objects.get(
            id=int(service_offering_id)
        )
        if get_service_plans:
            self.service_plans = ServicePlan.objects.filter(
                service_offering=self.service_offering
            )

    def process(self):
        return self
