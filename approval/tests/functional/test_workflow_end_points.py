import pytest
import json
from django.urls import reverse
from approval.tests.factories import TemplateFactory
from approval.tests.factories import WorkflowFactory


@pytest.mark.django_db
class TestWorkflowEndPoints:
    def test_workflow_list(self, api_client):
        WorkflowFactory()
        url = reverse("approval:workflow-list")
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)

        assert content["count"] == 1

    def test_workflow_retrieve(self, api_client):
        workflow = WorkflowFactory()
        url = reverse("approval:workflow-detail", args=(workflow.id,))
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)
        assert content["id"] == workflow.id

    def test_workflow_delete(self, api_client):
        workflow = WorkflowFactory()
        url = reverse("approval:workflow-detail", args=(workflow.id,))
        response = api_client.delete(url)

        assert response.status_code == 204

    def test_workflow_patch(self, api_client):
        workflow = WorkflowFactory()
        url = reverse("approval:workflow-detail", args=(workflow.id,))
        response = api_client.patch(url, {"name": "update"}, format="json")

        assert response.status_code == 200

    def test_workflow_put_not_supported(self, api_client):
        workflow = WorkflowFactory()
        url = reverse("approval:workflow-detail", args=(workflow.id,))
        response = api_client.put(url, {"name": "update"}, format="json")

        assert response.status_code == 405

    def test_workflow_post(self, api_client):
        template = TemplateFactory()
        url = reverse("approval:workflow-list")
        response = api_client.post(
            url,
            {
                "template": template.id,
                "name": "abcdef",
                "description": "abc",
            },
            format="json",
        )

        assert response.status_code == 201
