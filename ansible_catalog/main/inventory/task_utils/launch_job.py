""" Task to Launch a Job in Tower and wait for it to end"""
import time
import logging

from ansible_catalog.main.inventory.models import (
    ServiceInstance,
    ServiceOffering,
    ServicePlan,
)
from ansible_catalog.main.inventory.task_utils.tower_api import TowerAPI

logger = logging.getLogger("inventory")


class LaunchJob:
    """LaunchJob launches a job and waits for it to end"""

    REFRESH_INTERVAL = 10
    JOB_COMPLETION_STATUSES = ("successful", "failed", "error", "canceled")

    # default constructor
    def __init__(self, slug, body):
        self.tower = TowerAPI()
        self.slug = slug
        self.body = body

    # start processing
    def process(self):
        """Send a post request to start the job and wait for it to
        finish by polling the task status using get calls
        """
        attrs = (
            "id",
            "url",
            "artifacts",
            "name",
            "extra_vars",
            "created",
            "started",
            "finished",
            "status",
            "unified_job_template",
        )
        obj = self.tower.post(self.slug, self.body, attrs)
        while obj["status"] not in self.JOB_COMPLETION_STATUSES:
            time.sleep(self.REFRESH_INTERVAL)
            for obj in self.tower.get(obj["url"], attrs):
                pass

        if obj["status"] == "successful":
            instance = ServiceInstance.objects.create(
                **self._service_instance_options(obj)
            )
            logging.info("Service instance %d created", instance.id)

        return obj

    def _service_instance_options(self, output):
        service_offering = ServiceOffering.objects.get(
            source_ref=output["unified_job_template"]
        )
        service_plan = ServicePlan.objects.filter(
            service_offering=service_offering
        ).first()

        options = {}
        options["tenant_id"] = str(service_offering.tenant.id)
        options["source_id"] = str(service_offering.source.id)
        options["service_offering_id"] = str(service_offering.id)
        options["service_plan_id"] = (
            None if service_plan is None else str(service_plan.id)
        )
        options["external_url"] = output["url"]
        options["source_ref"] = output["id"]
        options["name"] = output["name"]
        options["source_created_at"] = output["created"]
        options["extra"] = {
            "status": output["status"],
            "started": output["started"],
            "finished": output["finished"],
            "extra_vars": output["extra_vars"],
            # TODO: need to add filtering with prefix: expose_to_cloud_redhat_come
            "artifacts": output["artifacts"],
        }

        return options
