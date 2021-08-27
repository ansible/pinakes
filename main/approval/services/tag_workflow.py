"""Unlink workflow service"""
import logging
from django.apps import apps

from main.approval.models import TagLink, Workflow

logger = logging.getLogger("approval")


class TagWorkflow:
    ADD = "tag_add"
    REMOVE = "tag_remove"
    FIND = "tag_find"

    def __init__(self, workflow=None, data=None):
        self.workflow = workflow
        self.data = data.copy() if data else {}
        self.params = (
            self.data if workflow is None else self.__tag_params(self.data)
        )
        self.object_id = self.data.pop("object_id", None)
        self.workflow_ids = []

    def process(self, operation):
        object_type = self.params.get("object_type")
        model = apps.get_model("main", object_type)
        instance = model.objects.get(id=self.object_id)

        if operation == TagWorkflow.ADD:
            instance.tags.add(self.__tag_name()["name"])

            obj, created = TagLink.objects.get_or_create(**self.params)
            if not created:
                logger.info("Tag ''{}'' is found".format(obj))
        elif operation == TagWorkflow.REMOVE:
            instance.tags.remove(self.__tag_name()["name"])
        elif operation == TagWorkflow.FIND:
            tag_names = [{"name": tag.name} for tag in instance.tags.all()]
            self.workflow_ids = [
                tag_link.workflow.id
                for tag_link in TagLink.objects.filter(**self.params).filter(
                    tag_name__in=tag_names
                )[::1]
            ]

        return self

    def find_workflows_by_tag_resources(self, tag_resources):
        if tag_resources is None:
            return []

        workflow_ids = []

        for resource in tag_resources:
            params = {
                "app_name": resource["app_name"],
                "object_type": resource["object_type"],
            }

            workflow_ids += [
                tag_link.workflow.id
                for tag_link in TagLink.objects.filter(**params).filter(
                    tag_name__in=resource["tags"]
                )[::1]
            ]

        return Workflow.objects.filter(id__in=list(set(workflow_ids)))

    def __tag_params(self, data):
        data["tenant_id"] = self.workflow.tenant.id
        data["workflow_id"] = self.workflow.id
        data["tag_name"] = self.__tag_name()

        return data

    def __tag_name(self):
        return {"name": "approval/workflows/{}".format(self.workflow.id)}
