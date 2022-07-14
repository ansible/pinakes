"""ServicePlanImport module imports the SurveySpec
    from Ansible Tower. It converts the Spec to DDF
    format and saves it in the DB
"""
import json
import logging
import hashlib

from django.utils import timezone
from pinakes.main.inventory.models import (
    InventoryServicePlan,
)

logger = logging.getLogger("inventory")


class ServicePlanImport:
    """Import Service Plan"""

    def __init__(self, tenant, source, tower, spec_converter):
        self.tenant = tenant
        self.source = source
        self.stats = {"adds": 0, "updates": 0}
        self.tower = tower
        self.spec_converter = spec_converter

    def get_stats(self):
        """Get the adds/updates for this object."""
        return self.stats

    def process(self, slug, service_offering_id, source_ref):
        """Fetch the Service Plan"""
        logger.info(f"Fetching survey spec {slug}")
        for new_obj in self.tower.get(slug, ["name", "description", "spec"]):
            if new_obj["name"] is None:
                logger.warning(
                    "No survey spec found even though survey_spec is enabled"
                )
            else:
                self._handle(new_obj, service_offering_id, source_ref)

    def _handle(self, data, service_offering_id, source_ref):
        """Convert the survey spec to DDF format and save it"""
        new_sha = self._get_sha256(data)
        now = timezone.now()
        old_obj = InventoryServicePlan.objects.filter(
            source_ref=source_ref, source=self.source
        ).first()
        if old_obj is None:
            logger.info(
                f"Creating new InventoryServicePlan source_ref {source_ref}"
            )
            self.stats["adds"] += 1
            ddf_data = self.spec_converter.process(data)
            InventoryServicePlan.objects.create(
                source_ref=source_ref,
                create_json_schema=ddf_data,
                schema_sha256=new_sha,
                source=self.source,
                tenant=self.tenant,
                service_offering_id=service_offering_id,
                source_created_at=now,
                source_updated_at=now,
                extra={},
            )
        elif old_obj.schema_sha256 != new_sha:
            logger.info(
                "Updating existing InventoryServicePlan source_ref"
                f" {source_ref}"
            )
            self.stats["updates"] += 1
            ddf_data = self.spec_converter.process(data)
            old_obj.create_json_schema = ddf_data
            old_obj.schema_sha256 = new_sha
            old_obj.source_updated_at = now
            old_obj.save()

    def _get_sha256(self, schema):
        hash_object = hashlib.sha256(json.dumps(schema).encode())
        return hash_object.hexdigest()
