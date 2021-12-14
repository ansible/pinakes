""" ServicePlanImport module imports the SurveySpec
    from Ansible Tower. It converts the Spec to DDF
    format and saves it in the DB
"""
import json
import hashlib

from django.utils import timezone
from ansible_catalog.main.inventory.models import InventoryServicePlan


class ServicePlanImport:
    """Import Service Plan"""

    def __init__(self, tenant, source, tower, spec_converter):
        self.tenant = tenant
        self.source = source
        self.stats = {}
        self.tower = tower
        self.spec_converter = spec_converter

    def process(self, slug, service_offering_id, source_ref):
        """Fetch the Service Plan"""
        for new_obj in self.tower.get(slug, ["name", "description", "spec"]):
            self._handle(new_obj, service_offering_id, source_ref)

    def _handle(self, data, service_offering_id, source_ref):
        """Convert the survey spec to DDF format and save it"""
        ddf_data = self.spec_converter.process(data)
        now = timezone.now()
        InventoryServicePlan.objects.create(
            source_ref=source_ref,
            create_json_schema=ddf_data,
            schema_sha256=self._get_sha256(ddf_data),
            source=self.source,
            tenant=self.tenant,
            service_offering_id=service_offering_id,
            source_created_at=now,
            source_updated_at=now,
            extra={},
        )

    def _get_sha256(self, schema):
        hash_object = hashlib.sha256(json.dumps(schema).encode())
        return hash_object.hexdigest()
