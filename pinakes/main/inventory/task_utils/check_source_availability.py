""" Task to Refresh Inventory from the Tower """
import logging
from django.db import transaction
from django.utils import timezone

from pinakes.main.models import Source

from pinakes.main.inventory.task_utils.controller_config import (
    ControllerConfig,
)
from pinakes.main.inventory.task_utils.tower_api import (
    TowerAPI,
)


logger = logging.getLogger("inventory")


class CheckSourceAvailability:
    """Check the availability of a given source"""

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

        self.source.last_checked_at = timezone.now()
        try:
            svc = ControllerConfig(self.tower).process()

            self.source.info = {}
            self.source.info["version"] = svc.tower_info["version"]
            self.source.info["url"] = svc.tower.url
            self.source.last_available_at = timezone.now()
            self.source.availability_status = "available"
            self.source.availability_message = "Check availability completed"
        except Exception as error:
            self.source.availability_status = "unavailable"
            self.source.availability_message = "Error: %s" % str(error)
            logger.error(
                "Check availability failed on %s: %s",
                self.tower.url,
                str(error),
            )

            # update refresh related fields in the same lock
            self.source.refresh_state = Source.State.FAILED
            self.source.last_refresh_message = (
                "{} is unavailable, refresh skipped".format(self.source.name)
            )
        finally:
            self.source.last_checked_at = timezone.now()

        self.source.save()
