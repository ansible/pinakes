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

    def process(self):
        self._pre_refresh()
        self._start_refresh()

    @transaction.atomic()
    def _pre_refresh(self):
        self.source = (
            Source.objects.select_for_update().filter(pk=self.source_id).get()
        )

        self.source.refresh_started_at = timezone.now()
        self.source.refresh_state = Source.State.IN_PROGRESS
        self.source.save()
        logger.info(f"Starting refresh on source {self.source_id}")

    @transaction.atomic()
    def _start_refresh(self):
        self.source = (
            Source.objects.select_for_update().filter(pk=self.source_id).get()
        )

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
            self.source.last_refresh_stats[
                "service_inventory"
            ] = sii.get_stats()

            soi = ServiceOfferingImport(
                self.source.tenant, self.source, self.tower, sii, plan_importer
            )
            logger.info("Fetching Job Templates & Workflows")
            soi.process()
            self.source.last_refresh_stats[
                "service_offering"
            ] = soi.get_stats()

            son = ServiceOfferingNodeImport(
                self.source.tenant, self.source, self.tower, sii, soi
            )
            logger.info("Fetching Workflow Template Nodes")
            son.process()
            self.source.last_refresh_stats[
                "service_offering_node"
            ] = son.get_stats()

            self.source.last_successful_refresh_at = timezone.now()
            self.source.refresh_state = Source.State.DONE
        except Exception as error:
            self.source.refresh_state = Source.State.FAILED
            self.source.last_refresh_message = str(error)
            logger.error("Refresh failed: %s", str(error))
            logger.error(traceback.format_exc())
        finally:
            self.source.refresh_finished_at = timezone.now()

        self.source.save()
