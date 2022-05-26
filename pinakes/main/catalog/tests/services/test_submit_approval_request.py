"""Test on CreateApprovalRequest service"""
import pytest

from pinakes.main.approval.models import Request
from pinakes.main.catalog.models import ApprovalRequest
from pinakes.main.catalog.services.submit_approval_request import (
    SubmitApprovalRequest,
)

from pinakes.main.catalog.tests.factories import (
    PortfolioFactory,
    PortfolioItemFactory,
    OrderFactory,
    OrderItemFactory,
)
from pinakes.main.inventory.tests.factories import (
    SourceFactory,
)


@pytest.mark.django_db
def test_submit_approval_request(mocker):
    """Test on creating ApprovalRequest service"""

    source = SourceFactory()

    portfolio = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(
        portfolio=portfolio, service_offering_source_ref=source.id
    )
    order = OrderFactory()
    order_item = OrderItemFactory(order=order, portfolio_item=portfolio_item)
    tag_resources = [
        {
            "app_name": "catalog",
            "object_type": "Portfolio",
            "tags": [{"name": "/abc"}],
        }
    ]

    mocker.patch("django_rq.enqueue")
    svc = SubmitApprovalRequest(tag_resources, order)
    svc.process()

    assert svc.order == order
    assert svc.order_item == order_item
    assert svc.tag_resources == tag_resources
    assert ApprovalRequest.objects.all().count() == 1
    assert Request.objects.all().count() == 1

    assert ApprovalRequest.objects.first().approval_request_ref == str(
        Request.objects.first().id
    )


@pytest.mark.django_db
def test_submit_approval_request_without_service_offering(mocker):
    portfolio = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(portfolio=portfolio)
    order = OrderFactory()
    OrderItemFactory(order=order, portfolio_item=portfolio_item)
    tag_resources = [
        {
            "app_name": "catalog",
            "object_type": "Portfolio",
            "tags": [{"name": "/abc"}],
        }
    ]

    mocker.patch("django_rq.enqueue")
    svc = SubmitApprovalRequest(tag_resources, order)
    svc.process()

    assert svc.order == order
    assert ApprovalRequest.objects.all().count() == 1
