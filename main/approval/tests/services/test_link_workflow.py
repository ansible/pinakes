"""Test tagging on the given workflow"""

import pytest

from main.approval.models import TagLink
from main.approval.services.link_workflow import LinkWorkflow
from main.approval.tests.factories import WorkflowFactory

from main.catalog.tests.factories import PortfolioFactory


@pytest.mark.django_db
def test_taglink_workflow_add_remove():
    """Test GET/REMOVE taglink on the a workflow"""
    workflow, portfolio, resource_obj = create_and_link()

    assert TagLink.objects.count() == 1
    assert portfolio.tags.count() == 1
    assert portfolio.tags.first().name == "approval/workflows/{}".format(
        portfolio.id
    )

    LinkWorkflow(workflow, resource_obj).process(LinkWorkflow.Operation.REMOVE)

    assert portfolio.tags.count() == 0
    assert TagLink.objects.count() == 1  # taglink should not be removed


@pytest.mark.django_db
def test_find_workflow_by_taglink():
    """Test FIND workflows by taglinks"""
    workflow, _portfolio, resource_obj = create_and_link()

    svc = LinkWorkflow(workflow, resource_obj)
    workflow_ids = svc.process(LinkWorkflow.Operation.FIND).workflow_ids

    assert workflow_ids == [workflow.id]


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
