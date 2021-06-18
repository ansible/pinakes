import pytest
import pdb

from approval.tests.factories import TemplateFactory
from approval.tests.factories import WorkflowFactory
from approval.tests.factories import TenantFactory


class TestWorkflows:
    @pytest.mark.django_db
    def test_workflow(self):
        tenant = TenantFactory()
        template = TemplateFactory(tenant=tenant)
        workflow = WorkflowFactory(tenant=tenant, template=template)
        assert tenant.id == workflow.tenant.id
        assert template.id == workflow.template.id

    @pytest.mark.django_db
    def test_empty_workflow_name(self):
        from django.db import IntegrityError

        tenant = TenantFactory()
        template = TemplateFactory(tenant=tenant)
        with pytest.raises(IntegrityError) as excinfo:
            WorkflowFactory(tenant=tenant, template=template, name="")

        assert "CHECK constraint failed: approval_workflow_name_empty" in str(
            excinfo.value
        )

    @pytest.mark.django_db
    def test_duplicate_workflow_name(self):
        from django.db import IntegrityError

        tenant = TenantFactory()
        template = TemplateFactory(tenant=tenant)
        name = "fred"
        WorkflowFactory(tenant=tenant, template=template, name=name)
        with pytest.raises(IntegrityError) as excinfo:
            WorkflowFactory(tenant=tenant, template=template, name=name)

        assert "UNIQUE constraint failed: approval_workflow.name" in str(excinfo.value)
