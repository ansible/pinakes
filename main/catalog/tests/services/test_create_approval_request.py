""" Test on CreateApprovalRequest service """
import pytest

from main.approval.models import Request
from main.catalog.models import ApprovalRequest
from main.catalog.services.create_approval_request import CreateApprovalRequest

from main.catalog.tests.factories import (
    PortfolioFactory,
    PortfolioItemFactory,
    OrderFactory,
    OrderItemFactory,
)
from main.inventory.tests.factories import (
    ServiceInventoryFactory,
    ServiceOfferingFactory,
    SourceFactory,
)


@pytest.mark.django_db
def test_create_approval_request():
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

    svc = CreateApprovalRequest(tag_resources, order_item)
    svc.process()

    assert svc.order == order
    assert svc.order_item == order_item
    assert svc.tag_resources == tag_resources
    assert ApprovalRequest.objects.all().count() == 1
    assert Request.objects.all().count() == 1

    assert ApprovalRequest.objects.first().approval_request_ref == str(
        Request.objects.first().id
    )
