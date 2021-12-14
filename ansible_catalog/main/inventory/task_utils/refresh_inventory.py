""" Task to Refresh Inventory from the Tower """
from django.utils import timezone

from ansible_catalog.main.models import Source, Tenant
from ansible_catalog.main.inventory.task_utils.service_inventory_import import (
    ServiceInventoryImport,
)
from ansible_catalog.main.inventory.task_utils.service_offering_import import (
    ServiceOfferingImport,
)
from ansible_catalog.main.inventory.task_utils.service_plan_import import (
    ServicePlanImport,
)
from ansible_catalog.main.inventory.task_utils.service_offering_node_import import (
    ServiceOfferingNodeImport,
)
from ansible_catalog.main.inventory.task_utils.tower_api import TowerAPI
from ansible_catalog.main.inventory.task_utils.spec_to_ddf import SpecToDDF


class RefreshInventory:
    """RefreshInventory imports objects from the tower"""

    # default constructor
    def __init__(self, tenant_id, source_id):
        self.tower = TowerAPI()
        self.source = Source.objects.get(pk=source_id)
        self.tenant = Tenant.objects.get(pk=tenant_id)

    # start processing
    def process(self):
        self.source.refresh_started_at = timezone.now()

        try:
            """Run the import process"""
            spec_converter = SpecToDDF()
            plan_importer = ServicePlanImport(
                self.tenant, self.source, self.tower, spec_converter
            )
            sii = ServiceInventoryImport(self.tenant, self.source, self.tower)
            print("Fetching Inventory")
            sii.process()
            self.source.last_refresh_message = (
                "Service Inventories: %s" % sii.get_stats()
            )

            soi = ServiceOfferingImport(
                self.tenant, self.source, self.tower, sii, plan_importer
            )
            print("Fetching Job Templates & Workflows")
            soi.process()
            self.source.last_refresh_message = (
                "%s; Job Templates & Workflows: %s"
                % (self.source.last_refresh_message, soi.get_stats())
            )

            son = ServiceOfferingNodeImport(
                self.tenant, self.source, self.tower, sii, soi
            )
            print("Fetching Workflow Template Nodes")
            son.process()
            self.source.last_refresh_message = (
                "%s; Workflow Template Nodes: %s"
                % (self.source.last_refresh_message, son.get_stats())
            )
            self.source.last_successful_refresh_at = timezone.now()
        except Exception as error:
            self.source.last_refresh_message = "Error: %s" % str(error)
        finally:
            self.source.refresh_finished_at = timezone.now()

        self.source.save()
