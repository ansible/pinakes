""" Get service plan for a given service plan id """

from ansible_catalog.main.inventory.models import InventoryServicePlan


class GetServicePlan:
    """Get service plan for a given service plan id"""

    def __init__(self, service_plan_id):
        self.service_plan = InventoryServicePlan.objects.get(
            id=int(service_plan_id)
        )

    def process(self):

        return self
