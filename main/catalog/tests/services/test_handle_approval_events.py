"""Test Notify Approval Request Service"""

import pytest

from main.approval.models import Request
from main.approval.tests.factories import RequestFactory

from main.catalog.models import ApprovalRequest, Order, ProgressMessage
from main.catalog.services.handle_approval_events import HandleApprovalEvents
from main.catalog.tests.factories import (
    ApprovalRequestFactory,
    OrderFactory,
)


@pytest.mark.django_db
def test_handle_approval_events_approved_completed():
    request = RequestFactory()
    order = OrderFactory()
    ApprovalRequestFactory(approval_request_ref=request.id, order=order)
    payload = {
        "request_id": request.id,
        "decision": "Approved",
        "reason": "Good work",
    }
    event = "request_finished"

    svc = HandleApprovalEvents(payload, event)
    svc.process()

    assert svc.approval_request.state == ApprovalRequest.State.APPROVED


@pytest.mark.django_db
def test_handle_approval_events_denied_completed():
    request = RequestFactory()
    order = OrderFactory()
    ApprovalRequestFactory(approval_request_ref=request.id, order=order)
    payload = {
        "request_id": request.id,
        "decision": "Denied",
        "reason": "Good work",
    }
    event = "request_finished"

    svc = HandleApprovalEvents(payload, event)
    svc.process()

    assert svc.approval_request.state == ApprovalRequest.State.DENIED


@pytest.mark.django_db
def test_handle_approval_events_canceled_complete():
    request = RequestFactory()
    order = OrderFactory()
    ApprovalRequestFactory(approval_request_ref=request.id, order=order)
    payload = {"request_id": request.id, "reason": "Bad request"}
    event = "request_canceled"

    svc = HandleApprovalEvents(payload, event)
    svc.process()

    assert svc.approval_request.state == ApprovalRequest.State.CANCELED


@pytest.mark.django_db
def test_handle_approval_events_raise_error(mocker):
    request = RequestFactory()
    order = OrderFactory()
    ApprovalRequestFactory(approval_request_ref=request.id, order=order)
    payload = {"request_id": request.id, "reason": "Bad request"}
    event = "request_finished"

    with mocker.patch(
        "main.catalog.services.start_order",
        side_effect=Exception("mocker error"),
    ):
        with pytest.raises(Exception):
            svc = HandleApprovalEvents(payload, event)
            svc.process()
        order.refresh_from_db()
        assert order.state == Order.State.FAILED
        assert (
            str(ProgressMessage.objects.last())
            == "Internal Error. Please contact our support team."
        )
