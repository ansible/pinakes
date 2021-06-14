import pytest
import json
from django.urls import reverse
from approval.tests.factories import TemplateFactory
from approval.tests.factories import WorkflowFactory
from approval.tests.factories import TenantFactory


@pytest.mark.django_db
class TestTemplateEndPoints:
    def test_template_list(self, api_client):
        TemplateFactory()
        url = reverse("approval:template-list")
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)

        assert content["count"] == 1

    def test_template_retrieve(self, api_client):
        template = TemplateFactory()
        url = reverse("approval:template-detail", args=(template.id,))
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)
        assert content["id"] == template.id

    def test_template_delete(self, api_client):
        template = TemplateFactory()
        url = reverse("approval:template-detail", args=(template.id,))
        response = api_client.delete(url)

        assert response.status_code == 204

    def test_template_patch(self, api_client):
        template = TemplateFactory()
        url = reverse("approval:template-detail", args=(template.id,))
        response = api_client.patch(url, {"title": "update"}, format="json")

        assert response.status_code == 200

    def test_portfolio_put_not_supported(self, api_client):
        template = TemplateFactory()
        url = reverse("approval:template-detail", args=(template.id,))
        response = api_client.put(url, {"title": "update"}, format="json")

        assert response.status_code == 405

    def test_template_post(self, api_client):
        TenantFactory()
        url = reverse("approval:template-list")
        response = api_client.post(
            url, {"title": "abcdef", "description": "abc"}, format="json"
        )

        assert response.status_code == 201

    def test_template_workflows_get(self, api_client):
        template = TemplateFactory()
        workflow = WorkflowFactory(template=template)
        url = reverse("approval:template-workflows", args=(template.id,))
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)

        assert content["count"] == 1
        assert content["results"][0]["id"] == workflow.id
