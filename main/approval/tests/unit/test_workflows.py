import pytest
from decimal import Decimal

from main.tests.factories import TenantFactory
from main.approval.tests.factories import TemplateFactory
from main.approval.tests.factories import WorkflowFactory


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

        assert f"CHECK constraint failed: {template._meta.app_label}_workflow_name_empty" in str(
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

        assert f"UNIQUE constraint failed: {template._meta.app_label}_workflow.name" in str(excinfo.value)

    @pytest.mark.django_db
    def test_duplicate_internal_sequence(self):
        from django.db import IntegrityError

        tenant = TenantFactory()
        template = TemplateFactory(tenant=tenant)
        name = "fred"
        WorkflowFactory(tenant=tenant, template=template, internal_sequence=Decimal(3))
        with pytest.raises(IntegrityError) as excinfo:
            WorkflowFactory(tenant=tenant, template=template, internal_sequence=Decimal(3))

        assert f"UNIQUE constraint failed: {template._meta.app_label}_workflow.internal_sequence" in str(excinfo.value)
