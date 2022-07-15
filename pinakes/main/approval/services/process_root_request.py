"""Process a root request"""
import logging
import django_rq

from pinakes.main.common import tasks
from pinakes.main.approval.models import (
    Request,
    Workflow,
    Action,
)
from pinakes.main.approval.services.create_action import (
    CreateAction,
)


logger = logging.getLogger("approval")


class ProcessRootRequest:
    """Create and start child requests, running by the worker"""

    def __init__(self, root_id, workflow_ids):
        self.request = Request.objects.get(pk=root_id)
        self.workflows = [Workflow.objects.get(pk=wid) for wid in workflow_ids]

    def process(self):
        self._create_child_requests()
        self._start_leaves()
        return self

    def _create_child_requests(self):
        if len(self.workflows) == 1 and len(self.workflows[0].group_refs) <= 1:
            if len(self.workflows[0].group_refs) == 0:
                group_ref = {}
            else:
                group_ref = self.workflows[0].group_refs[0]

            self._update_leaf_with_workflow(
                self.request,
                self.workflows[0],
                group_ref,
            )
            return

        for workflow in self.workflows:
            if len(workflow.group_refs) == 0:
                group_refs = [{}]
            else:
                group_refs = workflow.group_refs
            for group_ref in group_refs:
                child_request = self.request.create_child()
                self._update_leaf_with_workflow(
                    child_request, workflow, group_ref
                )

        self._update_root_group_name()

    def _update_leaf_with_workflow(self, leaf_request, workflow, group_ref):
        group_name = group_ref.get("name", "<NO_GROUP>")
        group_uuid = group_ref.get("uuid", "")
        if group_uuid:
            tasks.add_group_permissions(leaf_request, (group_uuid,), ("read",))
        Request.objects.filter(id=leaf_request.id).update(
            workflow=workflow,
            group_ref=group_uuid,
            group_name=group_name,
        )
        leaf_request.refresh_from_db()

    def _update_root_group_name(self):
        sub_groups = self.request.subrequests.order_by("id").values(
            "group_name"
        )
        all_names = ",".join(x["group_name"] for x in sub_groups)
        self.request.group_name = all_names
        self.request.save()

    def _start_leaves(self):
        from pinakes.main.approval.tasks import (
            start_request_task,
        )

        first_leaves = (self.request,)
        if self.request.is_parent():
            first_child = self.request.subrequests.order_by("id").first()
            first_leaves = Request.objects.filter(
                workflow=first_child.workflow, parent=self.request
            )

        if len(first_leaves) == 1:
            # single node
            leaf = first_leaves[0]
            logger.info("Directly starting request %d", leaf.id)
            CreateAction(leaf, {"operation": Action.Operation.START}).process()
        else:
            for leaf in first_leaves:
                self.job = django_rq.enqueue(start_request_task, leaf.id)
                logger.info(
                    "Enqueued job %s for sub request %d", self.job.id, leaf.id
                )
