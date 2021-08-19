""" Notify an approval request """

from django.utils import timezone

from main.catalog.models import ApprovalRequest
from main.catalog.services.approval_state_transition import (
    ApprovalStateTransition,
)


class NotifyApprovalRequest:
    """Notify an approval request"""

    EVENT_REQUEST_FINISHED = "request_finished"
    EVENT_REQUEST_CANCELED = "request_canceled"
    COMPLETED_EVENTS = [EVENT_REQUEST_FINISHED, EVENT_REQUEST_CANCELED]

    def __init__(self, payload, event):
        self.request_id = payload.pop("request_id")
        self.approval_request = ApprovalRequest.objects.get(
            approval_request_ref=self.request_id
        )
        self.payload = payload
        self.event = event

    def process(self):
        if self.event not in self.COMPLETED_EVENTS:
            return self

        try:
            self.__update_approval_request()
            ApprovalStateTransition(self.approval_request.order).process()
        except Exception as error:
            order = self.approval_request.order
            order.mark_failed(
                "Internal Error. Please contact our support team."
            )
            raise error

        return self

    def __update_approval_request(self):
        if self.event == self.EVENT_REQUEST_FINISHED:
            state = self.payload["decision"]
        elif self.event == self.EVENT_REQUEST_CANCELED:
            state = str(ApprovalRequest.State.CANCELED)

        self.approval_request.state = state
        self.approval_request.reason = self.payload["reason"]
        self.approval_request.request_completed_at = timezone.now()
