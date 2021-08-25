"""Unlink workflow service"""
import logging
from django.apps import apps

from main.approval.models import TagLink

logger = logging.getLogger("approval")

class TagWorkflow:
    ADD = "tag_add"
    REMOVE = "tag_remove"

    def __init__(self, workflow, data):
        self.workflow = workflow
        self.object_id = data.pop('object_id')
        self.params = self.__tag_params(data)

    def process(self, operation):
        object_type = self.params.get("object_type")
        model = apps.get_model('main', object_type)
        instance = model.objects.get(id=self.object_id)

        if operation == TagWorkflow.ADD:
            instance.tags.add(self.__tag_name()["name"])

            obj, created = TagLink.objects.get_or_create(self.params)
            if not created:
                logger.info("Tag ''{}'' is found".format(obj))
        elif operation == TagWorkflow.REMOVE:
            instance.tags.remove(self.__tag_name()["name"])

        return self

    def __tag_params(self, data):
        data["tenant_id"] = self.workflow.tenant.id
        data["workflow_id"] = self.workflow.id
        data["tag_name"] = self.__tag_name()

        return data

    def __tag_name(self):
        return {
            "name": "approval/workflows/{}".format(self.workflow.id)
        }
