""" Task to Refresh Inventory from the Tower """
import logging
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


logger = logging.getLogger("inventory")


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
            logger.info("Fetching Inventory")
            sii.process()

            soi = ServiceOfferingImport(
                self.tenant, self.source, self.tower, sii, plan_importer
            )
            logger.info("Fetching Job Templates & Workflows")
            soi.process()

            son = ServiceOfferingNodeImport(
                self.tenant, self.source, self.tower, sii, soi
            )
            logger.info("Fetching Workflow Template Nodes")
            son.process()

            self.source.last_refresh_message = self._set_last_refresh_message(
                sii, soi, son
            )
            self.source.last_successful_refresh_at = timezone.now()
            self.source.refresh_state = Source.State.DONE
            self.source.last_available_at = timezone.now()
            self.source.availability_status = "available"
            self.source.availability_message = "Available"
        except Exception as error:
            self.source.last_refresh_message = "Error: %s" % str(error)
            self.source.refresh_state = Source.State.FAILED
            self.source.availability_status = "unavailable"
            self.source.availability_message = "Unavailable"
            logger.error("Refresh failed: %s", str(error))
        finally:
            self.source.refresh_finished_at = timezone.now()
            self.source.last_checked_at = timezone.now()

        self.source.save()

    def _set_last_refresh_message(
        self,
        service_inventory_import,
        service_offering_import,
        service_offering_node_import,
    ):
        last_refresh_message = ""
        sii_stats = service_inventory_import.get_stats()
        soi_stats = service_offering_import.get_stats()
        son_stats = service_offering_node_import.get_stats()

        filtered_sii_stats = {
            key: value for key, value in sii_stats.items() if value > 0
        }
        filtered_soi_stats = {
            key: value for key, value in soi_stats.items() if value > 0
        }
        filtered_son_stats = {
            key: value for key, value in son_stats.items() if value > 0
        }

        if bool(filtered_sii_stats):
            last_refresh_message += (
                "Service Inventories: %s;\n" % filtered_sii_stats
            )

        if bool(filtered_soi_stats):
            last_refresh_message += (
                "Job Templates & Workflows: %s;\n" % filtered_soi_stats
            )

        if bool(filtered_son_stats):
            last_refresh_message += (
                "Workflow Template Nodes: %s" % filtered_son_stats
            )

        if not bool(last_refresh_message):
            last_refresh_message = "Nothing to update"

        return last_refresh_message
