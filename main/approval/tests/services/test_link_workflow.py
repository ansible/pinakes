"""Test tagging on the given workflow"""

import pytest

from main.approval.models import TagLink
from main.approval.services.link_workflow import LinkWorkflow
from main.approval.tests.factories import WorkflowFactory
from main.catalog.services.operate_tag import OperateTag

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

    svc = LinkWorkflow(workflow, data)
    svc.process(OperateTag.Operation.Add)

    assert TagLink.objects.count() == 1
    assert portfolio.tags.count() == 1
    assert portfolio.tags.first().name == "approval/workflows/{}".format(
        portfolio.id
    )

    svc.process(OperateTag.Operation.Remove)

    assert portfolio.tags.count() == 0
