""" Create an approval request """
import django_rq
import logging
from automation_services_catalog.main.approval.models import Request, RequestContext
from automation_services_catalog.main.approval.tasks import process_root_task
from automation_services_catalog.main.approval.services.link_workflow import FindWorkflows

logger = logging.getLogger("approval")


class CreateRequest:
    """Create an approval request"""

    def __init__(self, data):
        self.data = data
        self.request = None
        self.job = None

    def process(self):
        tag_resources = self.data.pop("tag_resources", list())
        workflows = FindWorkflows(tag_resources).process().workflows
        workflow_ids = [workflow.id for workflow in workflows]

        content = self.data.pop("content")
        request_context = RequestContext.objects.create(
            content=content, context={}
        )
        self.request = Request.objects.create(
            request_context=request_context, **self.data
        )

        self.job = django_rq.enqueue(
            process_root_task, self.request.id, workflow_ids
        )
        logger.info(
            "Enqueued job %s for root request %d and workflows %s",
            self.job.id,
            self.request.id,
            str(workflow_ids),
        )

        return self
