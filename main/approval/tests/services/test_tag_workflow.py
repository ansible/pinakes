"""Test tagging on the given workflow"""

import pytest

from main.approval.models import TagLink
from main.approval.services.tag_workflow import TagWorkflow
from main.approval.tests.factories import WorkflowFactory

from main.catalog.tests.factories import PortfolioFactory


@pytest.mark.django_db
def test_tag_workflow_operations():
    """Test GET/REMOVE tagging on the given workflow"""
    workflow = WorkflowFactory()
    portfolio = PortfolioFactory()
    data = {
        "object_type": "Portfolio",
        "object_id": portfolio.id,
        "app_name": "catalog",
    }

    svc = TagWorkflow(workflow, data)
    svc.process(TagWorkflow.ADD)

    assert TagLink.objects.count() == 1
    assert portfolio.tags.count() == 1
    assert portfolio.tags.first().name == "approval/workflows/{}".format(
        portfolio.id
    )

    svc.process(TagWorkflow.REMOVE)

    assert portfolio.tags.count() == 0


@pytest.mark.django_db
def test_tag_workflow_find_operation():
    workflow_1 = WorkflowFactory()
    workflow_2 = WorkflowFactory()
    workflow_3 = WorkflowFactory()

    portfolio_1 = PortfolioFactory()
    data = {
        "object_type": "Portfolio",
        "object_id": portfolio_1.id,
        "app_name": "catalog",
    }

    svc = TagWorkflow(workflow_1, data)
    svc.process(TagWorkflow.ADD)

    portfolio_2 = PortfolioFactory()
    data = {
        "object_type": "Portfolio",
        "object_id": portfolio_2.id,
        "app_name": "catalog",
    }

    svc = TagWorkflow(workflow_2, data)
    svc.process(TagWorkflow.ADD)

    svc = TagWorkflow(workflow_3, data)
    svc.process(TagWorkflow.ADD)

    assert portfolio_1.tags.count() == 1
    assert portfolio_2.tags.count() == 2
    assert TagLink.objects.count() == 3

    svc = TagWorkflow(None, data)
    workflow_ids = svc.process(TagWorkflow.FIND).workflow_ids

    assert workflow_ids == [workflow_2.id, workflow_3.id]


@pytest.mark.django_db
def test_find_workflows_by_tag_resources():
    workflow1 = WorkflowFactory()
    workflow2 = WorkflowFactory()

    portfolio = PortfolioFactory()
    data = {
        "object_type": "Portfolio",
        "object_id": portfolio.id,
        "app_name": "catalog",
    }

    svc = TagWorkflow(workflow1, data)
    svc.process(TagWorkflow.ADD)

    svc = TagWorkflow(workflow2, data)
    svc.process(TagWorkflow.ADD)

    resource1 = {
        "app_name": "catalog",
        "object_type": "Portfolio",
        "tags": [
            {"name": "approval/workflows/{}".format(workflow1.id)},
            {"name": "approval/workflows/{}".format(workflow2.id)},
        ],
    }

    resource2 = {
        "app_name": "catalog",
        "object_type": "PortfolioItem",
        "tags": [
            {"name": "approval/workflows/{}".format(workflow1.id)},
            {"name": "approval/workflows/{}".format(workflow2.id)},
        ],
    }
    tag_resources = [resource1, resource2]
    svc = TagWorkflow()

    workflows = svc.find_workflows_by_tag_resources(tag_resources)

    assert len(workflows) == 2
