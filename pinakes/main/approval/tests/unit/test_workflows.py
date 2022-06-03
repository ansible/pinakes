from decimal import Decimal
import pytest
import math

from pinakes.main.tests.factories import TenantFactory
from pinakes.main.approval.models import Workflow
from pinakes.main.approval.tests.factories import (
    TemplateFactory,
)
from pinakes.main.approval.tests.factories import (
    WorkflowFactory,
)


@pytest.mark.django_db
def test_workflow():
    tenant = TenantFactory()
    template = TemplateFactory(tenant=tenant)
    workflow = WorkflowFactory(tenant=tenant, template=template)
    assert tenant.id == workflow.tenant.id
    assert template.id == workflow.template.id


@pytest.mark.django_db
def test_empty_workflow_name():
    from django.db import IntegrityError

    tenant = TenantFactory()
    template = TemplateFactory(tenant=tenant)
    with pytest.raises(IntegrityError) as excinfo:
        WorkflowFactory(tenant=tenant, template=template, name="")

    assert (
        "CHECK constraint failed:"
        f" {template._meta.app_label}_workflow_name_empty"
        in str(excinfo.value)
    )


@pytest.mark.django_db
def test_duplicate_workflow_name():
    from django.db import IntegrityError

    tenant = TenantFactory()
    template = TemplateFactory(tenant=tenant)
    name = "fred"
    WorkflowFactory(tenant=tenant, template=template, name=name)
    with pytest.raises(IntegrityError) as excinfo:
        WorkflowFactory(tenant=tenant, template=template, name=name)

    assert (
        "UNIQUE constraint failed:"
        f" {template._meta.app_label}_workflow.name" in str(excinfo.value)
    )


@pytest.mark.django_db
def test_duplicate_internal_sequence():
    from django.db import IntegrityError

    tenant = TenantFactory()
    template = TemplateFactory(tenant=tenant)
    WorkflowFactory(
        tenant=tenant, template=template, internal_sequence=Decimal(3)
    )
    with pytest.raises(IntegrityError) as excinfo:
        WorkflowFactory(
            tenant=tenant, template=template, internal_sequence=Decimal(3)
        )

    assert (
        "UNIQUE constraint failed:"
        f" {template._meta.app_label}_workflow.internal_sequence"
        in str(excinfo.value)
    )


@pytest.fixture
def workflow_ids():
    return [WorkflowFactory().id for _ in range(5)]


def _all_ids():
    return list(Workflow.objects.values_list("id", flat=True))


@pytest.mark.django_db
def test_move_up(workflow_ids):
    Workflow.objects.get(id=workflow_ids[4]).move_internal_sequence(-2)
    assert _all_ids() == [
        workflow_ids[0],
        workflow_ids[1],
        workflow_ids[4],
        workflow_ids[2],
        workflow_ids[3],
    ]


@pytest.mark.django_db
def test_move_down(workflow_ids):
    Workflow.objects.get(id=workflow_ids[1]).move_internal_sequence(2)
    assert _all_ids() == [
        workflow_ids[0],
        workflow_ids[2],
        workflow_ids[3],
        workflow_ids[1],
        workflow_ids[4],
    ]


@pytest.mark.django_db
def test_move_top(workflow_ids):
    Workflow.objects.get(id=workflow_ids[2]).move_internal_sequence(-2)
    assert _all_ids() == [
        workflow_ids[2],
        workflow_ids[0],
        workflow_ids[1],
        workflow_ids[3],
        workflow_ids[4],
    ]


@pytest.mark.django_db
def test_move_bottom(workflow_ids):
    Workflow.objects.get(id=workflow_ids[3]).move_internal_sequence(1)
    assert _all_ids() == [
        workflow_ids[0],
        workflow_ids[1],
        workflow_ids[2],
        workflow_ids[4],
        workflow_ids[3],
    ]


@pytest.mark.django_db
def test_move_up_beyond(workflow_ids):
    Workflow.objects.get(id=workflow_ids[2]).move_internal_sequence(-20)
    assert _all_ids() == [
        workflow_ids[2],
        workflow_ids[0],
        workflow_ids[1],
        workflow_ids[3],
        workflow_ids[4],
    ]


@pytest.mark.django_db
def test_move_down_beyond(workflow_ids):
    Workflow.objects.get(id=workflow_ids[3]).move_internal_sequence(20)
    assert _all_ids() == [
        workflow_ids[0],
        workflow_ids[1],
        workflow_ids[2],
        workflow_ids[4],
        workflow_ids[3],
    ]


@pytest.mark.django_db
def test_move_top_explicitly(workflow_ids):
    Workflow.objects.get(id=workflow_ids[2]).move_internal_sequence(-math.inf)
    assert _all_ids() == [
        workflow_ids[2],
        workflow_ids[0],
        workflow_ids[1],
        workflow_ids[3],
        workflow_ids[4],
    ]


@pytest.mark.django_db
def test_move_bottom_explicitly(workflow_ids):
    Workflow.objects.get(id=workflow_ids[3]).move_internal_sequence(math.inf)
    assert _all_ids() == [
        workflow_ids[0],
        workflow_ids[1],
        workflow_ids[2],
        workflow_ids[4],
        workflow_ids[3],
    ]


@pytest.mark.django_db
def test_new_at_the_end(workflow_ids):
    workflow = WorkflowFactory()
    assert _all_ids() == [
        workflow_ids[0],
        workflow_ids[1],
        workflow_ids[2],
        workflow_ids[3],
        workflow_ids[4],
        workflow.id,
    ]


@pytest.mark.django_db
def test_delete_middle(workflow_ids):
    Workflow.objects.get(id=workflow_ids[3]).delete()
    assert _all_ids() == [
        workflow_ids[0],
        workflow_ids[1],
        workflow_ids[2],
        workflow_ids[4],
    ]
