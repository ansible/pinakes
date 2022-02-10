""" Test starting an order """

import pytest

from automation_services_catalog.main.approval.tests.factories import (
    RequestFactory,
)

from automation_services_catalog.main.catalog.models import (
    ApprovalRequest,
    ProgressMessage,
)
from automation_services_catalog.main.catalog.services.start_order import (
    StartOrder,
)
from automation_services_catalog.main.catalog.tests.factories import (
    ApprovalRequestFactory,
    OrderFactory,
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
