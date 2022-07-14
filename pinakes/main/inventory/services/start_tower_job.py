"""Module to start a Tower Job using Django_rq"""
import django_rq
from pinakes.main.inventory.models import (
    ServiceOffering,
    OfferingKind,
)
from pinakes.main.inventory.tasks import launch_tower_task


class StartTowerJob:
    """Class to start Tower Job"""

    def __init__(self, service_offering_id, params):
        self.service_offering = ServiceOffering.objects.filter(
            id=service_offering_id
        ).first()
        self.params = {}
        self.params["extra_vars"] = params["service_parameters"] or {}
        self.job = None

    def process(self):
        """Start background task and return the job id"""
        if self.service_offering.kind == OfferingKind.WORKFLOW:
            slug = (
                "/api/v2/workflow_job_templates/"
                f"{self.service_offering.source_ref}/launch/"
            )
        else:
            slug = (
                "/api/v2/job_templates/"
                f"{self.service_offering.source_ref}/launch/"
            )

        self.job = django_rq.enqueue(launch_tower_task, slug, self.params)
        return self

    def job_id(self):
        """Return the Job ID"""
        return self.job.id
