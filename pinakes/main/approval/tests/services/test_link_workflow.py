"""Test tagging on the given workflow"""

import pytest

from pinakes.main.approval.models import TagLink
from pinakes.main.approval.services.link_workflow import (
    LinkWorkflow,
    FindWorkflows,
)
from pinakes.main.approval.tests.factories import (
    WorkflowFactory,
)

from pinakes.main.catalog.tests.factories import (
    PortfolioFactory,
)


@pytest.mark.django_db
def test_taglink_workflow_add_remove():
    """Test GET/REMOVE taglink on the a workflow"""
    workflow, portfolio, resource_obj = create_and_link()

    assert TagLink.objects.count() == 1
    assert portfolio.tags.count() == 1
    assert portfolio.tags.first().name == f"/approval/workflows={portfolio.id}"

    LinkWorkflow(workflow, resource_obj).process(LinkWorkflow.Operation.REMOVE)

    assert portfolio.tags.count() == 0
    assert TagLink.objects.count() == 1  # taglink should not be removed


@pytest.mark.django_db
def test_find_workflow_by_taglink():
    """Test FIND workflows by taglinks"""
    workflow, _portfolio, resource_obj = create_and_link()

    svc = LinkWorkflow(None, resource_obj)
    workflow_ids = svc.process(LinkWorkflow.Operation.FIND).workflow_ids

    assert workflow_ids == [workflow.id]


@pytest.mark.django_db
def test_find_workflow_by_tags():
    """Test finding workflows by remote tags"""
    workflow, _portfolio, resource_obj = create_and_link()
    resource_obj.pop("object_id")
    resource_obj["tags"] = (f"/approval/workflows={workflow.id}",)

    found_workflows = FindWorkflows((resource_obj,)).process().workflows
    # assert len(found_workflows) == 1
    assert workflow.id == found_workflows[0].id


def create_and_link():
    workflow = WorkflowFactory()
    portfolio = PortfolioFactory()
    data = {
        "object_type": "Portfolio",
        "object_id": portfolio.id,
        "app_name": "catalog",
    }
    LinkWorkflow(workflow, data).process(LinkWorkflow.Operation.ADD)
    return workflow, portfolio, data
