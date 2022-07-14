"""Task to Refresh Inventory from the Tower"""
import logging
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from pinakes.main.models import Source

from pinakes.main.inventory.task_utils.controller_config import (
    ControllerConfig,
)
from pinakes.main.inventory.task_utils.tower_api import (
    TowerAPI,
)

from pinakes.main.inventory.exceptions import (
    SourceUnchangeableException,
)

logger = logging.getLogger("inventory")


class CheckSourceAvailability:
    """Check the availability of a given source"""

    def __init__(self, source_id):
        self.tower = TowerAPI()
        self.source_id = source_id
        self.error_dict = {}

    @transaction.atomic()
    def process(self):
        self.source = (
            Source.objects.filter(pk=self.source_id)
            .select_for_update(nowait=True)
            .get()
        )

        self.source.last_checked_at = timezone.now()
        self.source.availability_status = "unknown"
        self.source.availability_message = "Starting check availability"
        self.source.save()
        try:
            svc = ControllerConfig(self.tower).process()

            self._check_source_changed(svc)
            self.source.info = {}
            self.source.info["install_uuid"] = svc.tower_info["install_uuid"]
            self.source.info["url"] = svc.tower.url

            self.source.info["version"] = svc.tower_info["version"]
            self.source.last_available_at = timezone.now()
            self.source.availability_status = "available"
            self.source.availability_message = _(
                "Check availability completed"
            )
        except SourceUnchangeableException as error:
            self.source.availability_status = "unavailable"
            self.source.availability_message = str(error)
            logger.error(
                "Source has changed, check availability failed on %s: %s",
                self.tower.url,
                str(self.error_dict),
            )

            self.source.refresh_state = Source.State.FAILED
            self.source.error_code = Source.ErrorCode.SOURCE_CANNOT_BE_CHANGED
            self.source.error_dict = self.error_dict
        except Exception as error:
            self.source.availability_status = "unavailable"
            self.source.availability_message = str(error)
            logger.error(
                "Check availability failed on %s: %s",
                self.tower.url,
                str(error),
            )

            # update refresh related fields in the same lock
            self.source.refresh_state = Source.State.FAILED
        finally:
            self.source.last_checked_at = timezone.now()

        self.source.save()

    def _check_source_changed(self, svc):
        if (
            isinstance(self.source.info, dict)
            and "install_uuid" in self.source.info
        ):
            if (
                self.source.info["install_uuid"]
                != svc.tower_info["install_uuid"]
            ):
                self.error_dict["new_url"] = svc.tower.url
                self.error_dict["new_install_uuid"] = svc.tower_info[
                    "install_uuid"
                ]
                raise SourceUnchangeableException(
                    "Once assigned source cannot be changed"
                )
