""" A Service object to compare the Catalog service plan
    with the Inventory service plan and if they are different
    Copy over the changes if the admin has not modified the schema
    if the admin has modified the schema then flag the service plan
    as outdated so it can be reset
"""
import logging
from django.core.exceptions import ObjectDoesNotExist

from ansible_catalog.main.inventory.models import InventoryServicePlan
from ansible_catalog.main.catalog.models import ServicePlan
from ansible_catalog.main.catalog.services.refresh_service_plan import (
    RefreshServicePlan,
)

logger = logging.getLogger("catalog")


class UpdateServicePlans:
    def __init__(self, tenant_id, source_id):
        self.tenant_id = tenant_id
        self.source_id = source_id
        self.updated = 0

    def process(self):
        sps = ServicePlan.objects.filter(
            tenant_id=self.tenant_id, outdated=False
        )
        for sp in sps:
            svc = RefreshServicePlan(sp).process()
            if svc.is_updated:
                self.updated += 1

        return self
