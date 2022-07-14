"""Create an approval request"""
import logging
import django_rq
from pinakes.main.approval.models import (
    Request,
    RequestContext,
)
from pinakes.main.approval.tasks import process_root_task
from pinakes.main.approval.services.link_workflow import (
    FindWorkflows,
)
from pinakes.main.approval import validations

logger = logging.getLogger("approval")


class CreateRequest:
    """Create an approval request"""

    def __init__(self, data, context=None):
        self.data = data
        if context is None:
            context = {}
        self.context = context
        self.request = None
        self.job = None

    def process(self):
        logger.info("Creating request from data %s", self.data)
        tag_resources = self.data.pop("tag_resources", [])
        workflows = FindWorkflows(tag_resources).process().workflows
        for workflow in workflows:
            validations.validate_and_update_approver_groups(workflow)

        workflow_ids = [workflow.id for workflow in workflows]

        content = self.data.pop("content")
        request_context = RequestContext.objects.create(
            content=content, context=self.context
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
