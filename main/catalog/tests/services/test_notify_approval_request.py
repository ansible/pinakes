"""Test Notify Approval Request Service"""

import pytest

from main.approval.models import Request
from main.approval.tests.factories import RequestFactory

from main.catalog.models import ApprovalRequest, Order
from main.catalog.services.notify_approval_request import NotifyApprovalRequest
from main.catalog.tests.factories import (
    ApprovalRequestFactory,
    OrderFactory,
)


@pytest.mark.django_db
def test_notify_approval_request_approved_completed():
    request = RequestFactory()
    order = OrderFactory()
    ApprovalRequestFactory(approval_request_ref=request.id, order=order)
    payload = {
        "request_id": request.id,
        "decision": "Approved",
        "reason": "Good work",
    }
    event = "request_finished"

    svc = NotifyApprovalRequest(payload, event)
    svc.process()

    assert svc.approval_request.state == ApprovalRequest.State.APPROVED


@pytest.mark.django_db
def test_notify_approval_request_denied_completed():
    request = RequestFactory()
    order = OrderFactory()
    ApprovalRequestFactory(approval_request_ref=request.id, order=order)
    payload = {
        "request_id": request.id,
        "decision": "Denied",
        "reason": "Good work",
    }
    event = "request_finished"

    svc = NotifyApprovalRequest(payload, event)
    svc.process()

    assert svc.approval_request.state == ApprovalRequest.State.DENIED


@pytest.mark.django_db
def test_notify_approval_request_canceled():
    request = RequestFactory()
    order = OrderFactory()
    ApprovalRequestFactory(approval_request_ref=request.id, order=order)
    payload = {"request_id": request.id, "reason": "Bad request"}
    event = "request_canceled"

    svc = NotifyApprovalRequest(payload, event)
    svc.process()

    assert svc.approval_request.state == ApprovalRequest.State.CANCELED
