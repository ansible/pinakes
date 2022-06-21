import pytest

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
    WorkflowFactory(tenant=tenant, template=template, internal_sequence=3)
    with pytest.raises(IntegrityError) as excinfo:
        WorkflowFactory(tenant=tenant, template=template, internal_sequence=3)

    assert (
        "UNIQUE constraint failed:"
        f" {template._meta.app_label}_workflow.internal_sequence"
        in str(excinfo.value)
    )


@pytest.fixture
def workflow_ids(request):
    return [
        WorkflowFactory(internal_sequence=r * request.param).id
        for r in range(1, 6)
    ]


def _all_ids():
    return list(Workflow.objects.values_list("id", flat=True))


def _move_sequence(id, delta):
    workflow = Workflow.objects.get(id=id)
    workflow.move_internal_sequence(delta)
    workflow.save()


@pytest.mark.django_db
@pytest.mark.parametrize("workflow_ids", [1024, 1], indirect=True)
def test_move_up(workflow_ids):
    _move_sequence(workflow_ids[4], -2)
    assert _all_ids() == [
        workflow_ids[0],
        workflow_ids[1],
        workflow_ids[4],
        workflow_ids[2],
        workflow_ids[3],
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("workflow_ids", [1024, 1], indirect=True)
def test_move_down(workflow_ids):
    _move_sequence(workflow_ids[1], 2)
    assert _all_ids() == [
        workflow_ids[0],
        workflow_ids[2],
        workflow_ids[3],
        workflow_ids[1],
        workflow_ids[4],
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("workflow_ids", [1024, 1], indirect=True)
def test_move_top(workflow_ids):
    _move_sequence(workflow_ids[2], -2)
    assert _all_ids() == [
        workflow_ids[2],
        workflow_ids[0],
        workflow_ids[1],
        workflow_ids[3],
        workflow_ids[4],
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("workflow_ids", [1024, 1], indirect=True)
def test_move_bottom(workflow_ids):
    _move_sequence(workflow_ids[3], 1)
    assert _all_ids() == [
        workflow_ids[0],
        workflow_ids[1],
        workflow_ids[2],
        workflow_ids[4],
        workflow_ids[3],
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("workflow_ids", [1024, 1], indirect=True)
def test_move_up_beyond(workflow_ids):
    _move_sequence(workflow_ids[2], -20)
    assert _all_ids() == [
        workflow_ids[2],
        workflow_ids[0],
        workflow_ids[1],
        workflow_ids[3],
        workflow_ids[4],
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("workflow_ids", [1024, 1], indirect=True)
def test_move_down_beyond(workflow_ids):
    _move_sequence(workflow_ids[3], 20)
    assert _all_ids() == [
        workflow_ids[0],
        workflow_ids[1],
        workflow_ids[2],
        workflow_ids[4],
        workflow_ids[3],
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("workflow_ids", [1024, 1], indirect=True)
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
@pytest.mark.parametrize("workflow_ids", [1024, 1], indirect=True)
def test_delete_middle(workflow_ids):
    Workflow.objects.get(id=workflow_ids[3]).delete()
    assert _all_ids() == [
        workflow_ids[0],
        workflow_ids[1],
        workflow_ids[2],
        workflow_ids[4],
    ]
