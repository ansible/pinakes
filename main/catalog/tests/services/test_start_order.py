""" Test starting an order """

import pytest

from main.approval.models import Request
from main.approval.tests.factories import RequestFactory

from main.catalog.models import (
    ApprovalRequest,
    Order,
    OrderItem,
    ProgressMessage,
)
from main.catalog.services.start_order import StartOrder
from main.catalog.tests.factories import (
    ApprovalRequestFactory,
    OrderFactory,
    OrderItemFactory,
)


@pytest.mark.django_db
def test_start_to_place_order():
    request = RequestFactory()
    order = OrderFactory()
    ApprovalRequestFactory(
        state=ApprovalRequest.State.APPROVED,
        reason="Approved",
        approval_request_ref=request.id,
        order=order,
    )

    svc = StartOrder(order)
    svc.process()

    assert (
        str(ProgressMessage.objects.last()) == f"Order {order.id} is completed"
    )
