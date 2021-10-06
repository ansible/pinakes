""" Create an approval request """
import django_rq
import logging
from ansible_catalog.main.approval.models import Request, RequestContext
from ansible_catalog.main.approval.tasks import start_request_task
from ansible_catalog.main.approval.services.link_workflow import LinkWorkflow

logger = logging.getLogger("approval")

SYSTEM_APPROVAL = "System approval"

class CreateRequest:
    """Create an approval request"""

    def __init__(self, data):
        self.data = data
        self.request = None
        self.job = None
        self.workflows = ()

    def process(self):
        tag_resources = self.data.pop("tag_resources", None)
        self.workflows = LinkWorkflow().find_workflows_by_tag_resources(tag_resources)

        content = self.data.pop("content")
        request_context = RequestContext.objects.create(
            content=content, context={}
        )
        self.request = Request.objects.create(
            request_context=request_context, **self.data
        )
        self._create_child_requests()
        self._start_leaves()

        return self

    def _create_child_requests(self):
        if len(self.workflows) == 1 and len(self.workflows[0].group_refs) == 1:
            self._update_leaf_with_workflow(self.request, self.workflows[0], self.workflows[0].group_refs[0])
            return

        for workflow in self.workflows:
            for group_ref in workflow.group_refs:
                child_request = self.request.create_child()
                self._update_leaf_with_workflow(child_request, workflow, group_ref)

        self._update_root_group_name()
        return

    def _update_leaf_with_workflow(self, leaf_request, workflow, group_ref):
        group_name = group_ref.get("name") or SYSTEM_APPROVAL
        Request.objects.filter(id=leaf_request.id).update(workflow=workflow, group_ref=group_ref.get("uuid"), group_name=group_name)

    def _update_root_group_name(self):
        sub_groups = self.request.subrequests.order_by("id").values("group_name")
        all_names = ",".join(map(lambda x: x["group_name"], sub_groups))
        self.request.group_name = all_names
        self.request.save()

    def _start_leaves(self):
        first_leaves = (self.request,)
        if self.request.is_parent:
            first_child = self.request.subrequests.order_by("id").first()
            first_leaves = Request.objects.filter(workflow=first_child.workflow)

        for leaf in first_leaves:
            django_rq.enqueue(start_request_task, leaf.id)
            logger.info(
                "Enqueued job %s for request %d", self.job.id, leaf.id
            )
