""" Task to Refresh Inventory from the Tower """
import logging
import traceback
from django.db import transaction
from django.utils import timezone

from pinakes.main.models import Source
from pinakes.main.inventory.task_utils.service_inventory_import import (
    ServiceInventoryImport,
)
from pinakes.main.inventory.task_utils.service_offering_import import (
    ServiceOfferingImport,
)
from pinakes.main.inventory.task_utils.service_plan_import import (
    ServicePlanImport,
)
from pinakes.main.inventory.task_utils.service_offering_node_import import (
    ServiceOfferingNodeImport,
)
from pinakes.main.inventory.task_utils.tower_api import (
    TowerAPI,
)
from pinakes.main.inventory.task_utils.spec_to_ddf import (
    SpecToDDF,
)


logger = logging.getLogger("inventory")


class RefreshInventory:
    """RefreshInventory imports objects from the tower"""

    # default constructor
    def __init__(self, source_id):
        self.tower = TowerAPI()
        self.source_id = source_id

    @transaction.atomic()
    def process(self):
        self.source = (
            Source.objects.filter(pk=self.source_id)
            .select_for_update(nowait=True)
            .get()
        )

        self.source.refresh_started_at = timezone.now()
        self.source.refresh_state = Source.State.INPROGRESS
        self.source.save()

        try:
            """Run the import process"""
            spec_converter = SpecToDDF()
            plan_importer = ServicePlanImport(
                self.source.tenant, self.source, self.tower, spec_converter
            )
            sii = ServiceInventoryImport(
                self.source.tenant, self.source, self.tower
            )
            logger.info("Fetching Inventory")
            sii.process()

            soi = ServiceOfferingImport(
                self.source.tenant, self.source, self.tower, sii, plan_importer
            )
            logger.info("Fetching Job Templates & Workflows")
            soi.process()

            son = ServiceOfferingNodeImport(
                self.source.tenant, self.source, self.tower, sii, soi
            )
            logger.info("Fetching Workflow Template Nodes")
            son.process()

            self.source.last_refresh_message = self._set_last_refresh_message(
                sii, soi, son
            )
            self.source.last_successful_refresh_at = timezone.now()
            self.source.refresh_state = Source.State.DONE
        except Exception as error:
            self.source.last_refresh_message = "Error: %s" % str(error)
            self.source.refresh_state = Source.State.FAILED
            logger.error("Refresh failed: %s", str(error))
            logger.error(traceback.format_exc())
        finally:
            self.source.refresh_finished_at = timezone.now()

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
