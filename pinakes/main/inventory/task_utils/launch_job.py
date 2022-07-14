"""Task to Launch a Job in Tower and wait for it to end"""
import time
import logging
from django.utils.translation import gettext_lazy as _
from pinakes.main.inventory.models import (
    InventoryServicePlan,
    ServiceInstance,
    ServiceOffering,
)
from pinakes.main.inventory.task_utils.tower_api import (
    TowerAPI,
)

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
        self.output = None
        self.service_instance_ref = None

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
            obj = next(self.tower.get(obj["url"], attrs))

        self.output = obj

        if obj["status"] == "successful":
            instance = ServiceInstance.objects.create(
                **self._service_instance_options()
            )
            self.service_instance_ref = str(instance.id)
            logger.info("Service instance %d created", instance.id)
        else:
            logger.error(
                "Job [%s] has [%s] status", str(obj["id"]), obj["status"]
            )
            raise RuntimeError(
                _("Job %(id)s has %(status)s status")
                % {"id": str(obj["id"]), "status": obj["status"]}
            )

        return self

    def _service_instance_options(self):
        service_offering = ServiceOffering.objects.get(
            source_ref=self.output["unified_job_template"]
        )
        service_plan = InventoryServicePlan.objects.filter(
            service_offering=service_offering
        ).first()

        options = {}
        options["tenant_id"] = str(service_offering.tenant.id)
        options["source_id"] = str(service_offering.source.id)
        options["service_offering_id"] = str(service_offering.id)
        options["service_plan_id"] = (
            None if service_plan is None else str(service_plan.id)
        )
        options["external_url"] = self.output.get("url", None)
        options["source_ref"] = self.output.get("id", None)
        options["name"] = self.output.get("name", None)
        options["source_created_at"] = self.output.get("created", None)
        options["extra"] = {
            "status": self.output.get("status", None),
            "started": self.output.get("started", None),
            "finished": self.output.get("finished", None),
            "extra_vars": self.output.get("extra_vars", None),
            # TODO(hsong-rh): need to add filtering with prefix:
            #  expose_to_cloud_redhat_come
            "artifacts": self.output.get("artifacts", None),
        }

        return options
