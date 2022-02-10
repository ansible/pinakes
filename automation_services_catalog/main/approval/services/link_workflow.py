"""services for linking/unliking/finding workflows"""
import logging
from django.apps import apps
from enum import Enum

from automation_services_catalog.main.approval.models import TagLink, Workflow
from automation_services_catalog.main.catalog.services.operate_tag import (
    OperateTag,
)

logger = logging.getLogger("approval")


class LinkWorkflow:
    """Link workflow with tags"""

    Operation = Enum("Operation", ["ADD", "REMOVE", "FIND"])

    def __init__(self, workflow=None, data=None):
        self.workflow = workflow
        self.params = (
            data.copy() if workflow is None else self._tag_params(data)
        )
        self.object_id = data.get("object_id", None)
        self.workflow_ids = []

    def process(self, operation):
        object_type = self.params.get("object_type")
        model = apps.get_model("main", object_type)
        instance = model.objects.get(id=self.object_id)

        if operation == self.Operation.ADD:
            OperateTag(instance).process(
                OperateTag.Operation.ADD, self._tag_name()
            )
            obj, created = TagLink.objects.get_or_create(**self.params)
            if not created:
                logger.info("Tag '%s' is found", obj)
        elif operation == self.Operation.REMOVE:
            OperateTag(instance).process(
                OperateTag.Operation.REMOVE, self._tag_name()
            )
        elif operation == self.Operation.FIND:
            tag_names = [tag.name for tag in instance.tags.all()]
            self.workflow_ids = [
                tag_link.workflow.id
                for tag_link in TagLink.objects.filter(
                    object_type=self.params["object_type"]
                ).filter(tag_name__in=tag_names)
            ]

        return self

    def _tag_params(self, data):
        params = data.copy()
        params["tenant_id"] = self.workflow.tenant.id
        params["workflow_id"] = self.workflow.id
        params["tag_name"] = self._tag_name()
        params.pop("object_id")

        return params

    def _tag_name(self):
        return "/approval/workflows={}".format(self.workflow.id)


class FindWorkflows:
    """Find workflows by remote tags"""

    def __init__(self, tag_resources):
        self.tag_resources = tag_resources
        self.workflows = ()

    def process(self):
        workflows = set()
        for resource in self.tag_resources:
            params = {
                "app_name": resource["app_name"],
                "object_type": resource["object_type"],
            }

            for link in TagLink.objects.filter(**params).filter(
                tag_name__in=resource["tags"]
            ):
                workflows.add(link.workflow)

        self.workflows = list(workflows)

        return self
