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
            try:
                isp = InventoryServicePlan.objects.get(
                    pk=sp.inventory_service_plan_ref
                )
            except ObjectDoesNotExist:
                logger.error(
                    f"Inventory Service Plan {sp.inventory_service_plan_ref} doesn't exist"
                )
                # TODO: Maybe we need to mark this portfolio as broken
                continue

            if isp.schema_sha256 != sp.base_sha256:
                if sp.modified:
                    sp.outdated = True
                    sp.outdated_changes = "Some changes have been detected in schema"  # TODO: Call compare service
                else:
                    sp.base_schema = isp.create_json_schema
                    sp.base_sha256 = isp.schema_sha256
                sp.save()
                self.updated += 1

        return self
