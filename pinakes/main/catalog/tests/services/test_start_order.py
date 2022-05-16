"""Test starting an order"""

import pytest

from pinakes.main.approval.tests.factories import (
    RequestFactory,
)

from pinakes.main.catalog.models import (
    ApprovalRequest,
    ProgressMessage,
)
from pinakes.main.catalog.services.start_order import (
    StartOrder,
)
from pinakes.main.catalog.tests.factories import (
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

    assert "Order %(order_id)s is completed" == str(
        ProgressMessage.objects.last()
    )
