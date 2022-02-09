""" Test starting an order """

import pytest

from automation_services_catalog.main.approval.tests.factories import RequestFactory

from automation_services_catalog.main.catalog.models import (
    ApprovalRequest,
    Order,
    ProgressMessage,
)
from automation_services_catalog.main.catalog.services.finish_order import FinishOrder
from automation_services_catalog.main.catalog.tests.factories import (
    ApprovalRequestFactory,
    OrderFactory,
    OrderItemFactory,
)


@pytest.mark.django_db
def test_start_to_finish_order():
    request = RequestFactory()
    order = OrderFactory()
    order_item = OrderItemFactory(
        order=order, service_parameters_raw={"a": "b"}
    )
    ApprovalRequestFactory(
        state=ApprovalRequest.State.CANCELED,
        reason="Bad request",
        approval_request_ref=request.id,
        order=order,
    )

    svc = FinishOrder(order)
    svc.process(is_complete=False)
    order.refresh_from_db()
    order_item.refresh_from_db()

    assert (
        str(ProgressMessage.objects.last())
        == "This order item has failed due to the entire order canceled before it ran"
    )
    assert order.state == Order.State.FAILED
    assert order_item.service_parameters_raw is None
