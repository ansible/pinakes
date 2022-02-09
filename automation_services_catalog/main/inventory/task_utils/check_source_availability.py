""" Task to Refresh Inventory from the Tower """
import logging
from django.conf import settings
from django.utils import timezone

from automation_services_catalog.main.models import Source, Tenant

from automation_services_catalog.main.inventory.task_utils.controller_config import (
    ControllerConfig,
)
from automation_services_catalog.main.inventory.task_utils.tower_api import TowerAPI


logger = logging.getLogger("inventory")


class CheckSourceAvailability:
    """Check the availability of a given source"""

    def __init__(self, tenant_id, source_id):
        self.tower = TowerAPI()
        self.source = Source.objects.get(pk=source_id)
        self.tenant = Tenant.objects.get(pk=tenant_id)

    def process(self):
        self.source.last_checked_at = timezone.now()
        try:
            svc = ControllerConfig(self.tower).process()

            self.source.info = {}
            self.source.info["version"] = svc.tower_info["version"]
            self.source.info["url"] = svc.tower.url
            self.source.last_available_at = timezone.now()
            self.source.availability_status = "available"
            self.source.availability_message = "Available"
        except Exception as error:
            self.source.availability_status = "unavailable"
            self.source.availability_message = "Unavailable"
            logger.error("Check availability failed: %s", str(error))
        finally:
            self.source.last_checked_at = timezone.now()

        self.source.save()
