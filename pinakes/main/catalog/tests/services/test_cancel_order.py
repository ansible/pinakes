""" Test on CancelOrder service """
import pytest

from pinakes.main.approval.models import Action, Request
from pinakes.main.catalog.models import Order
from pinakes.main.catalog.exceptions import (
    UncancelableException,
)
from pinakes.main.catalog.services.cancel_order import (
    CancelOrder,
)

from pinakes.main.approval.tests.factories import (
    RequestFactory,
)
from pinakes.main.catalog.tests.factories import (
    ApprovalRequestFactory,
    OrderFactory,
)


@pytest.mark.django_db
def test_cancel_order():
    approval_request = RequestFactory()
    order = OrderFactory()
    ApprovalRequestFactory(
        order=order, approval_request_ref=str(approval_request.id)
    )

    svc = CancelOrder(order)
    svc.process()

    approval_request.refresh_from_db()

    assert order.state == Order.State.CANCELED
    assert approval_request.state == Request.State.CANCELED
    assert Action.objects.count() == 1
    assert Action.objects.first().operation == Action.Operation.CANCEL


@pytest.mark.django_db
def test_cancel_order_with_uncancelable_states():
    approval_request = RequestFactory()

    for state in [
        Order.State.ORDERED,
        Order.State.FAILED,
        Order.State.COMPLETED,
    ]:
        order = OrderFactory(state=state)
        ApprovalRequestFactory(
            order=order, approval_request_ref=str(approval_request.id)
        )

        svc = CancelOrder(order)
        with pytest.raises(UncancelableException) as excinfo:
            svc.process()

        assert str(excinfo.value) == (
            "Order {} is not cancelable in its current state: {}"
        ).format(order.id, order.state)
