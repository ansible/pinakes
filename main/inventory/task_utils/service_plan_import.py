""" ServicePlanImport module imports the SurveySpec
    from Ansible Tower. It converts the Spec to DDF
    format and saves it in the DB
"""

import json
from django.utils import timezone
from main.inventory.models import ServicePlan


class ServicePlanImport:
    """Import Service Plan"""

    def __init__(self, tenant, source, tower, spec_converter):
        self.tenant = tenant
        self.source = source
        self.stats = {}
        self.tower = tower
        self.spec_converter = spec_converter

    def process(self, slug, service_offering_id, source_ref):
        """ Fetch the Service Plan """
        for new_obj in self.tower.get(slug, ["name", "description", "spec"]):
            self.__handle(new_obj, service_offering_id, source_ref)

    def __handle(self, data, service_offering_id, source_ref):
        """ Convert the survey spec to DDF format and save it"""
        ddf_data = self.spec_converter.process(data)
        now = timezone.now()
        ServicePlan.objects.create(
            source_ref=source_ref,
            create_json_schema=json.dumps(ddf_data),
            source=self.source,
            tenant=self.tenant,
            service_offering_id=service_offering_id,
            source_created_at=now,
            source_updated_at=now,
            extra={},
        )
