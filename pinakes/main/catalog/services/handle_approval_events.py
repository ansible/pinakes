"""Handle approval events"""
import logging

from django.utils import timezone
from django.utils.translation import gettext_noop

from pinakes.main.catalog.models import (
    ApprovalRequest,
    ProgressMessage,
)

from pinakes.main.catalog.services.remove_approval_tags import (
    RemoveApprovalTags,
)
from pinakes.main.catalog.services.start_order import (
    StartOrder,
)
from pinakes.main.catalog.services.finish_order import (
    FinishOrder,
)

logger = logging.getLogger("catalog")


class HandleApprovalEvents:
    """Handle approval events"""

    EVENT_REQUEST_FINISHED = "request_finished"
    EVENT_REQUEST_CANCELED = "request_canceled"
    EVENT_WORKFLOW_DELETED = "workflow_deleted"
    COMPLETED_EVENTS = [EVENT_REQUEST_FINISHED, EVENT_REQUEST_CANCELED]

    def __init__(self, payload, event):
        self.payload = payload
        self.event = event

    def process(self):
        try:
            if self.event == self.EVENT_WORKFLOW_DELETED:
                workflow_id = self.payload.get("workflow_id")

                RemoveApprovalTags(workflow_id)
                return self

            if self.event not in self.COMPLETED_EVENTS:
                logger.warning("Event %s is skipped", self.event)
                return self

            request_id = self.payload.pop("request_id")
            self.approval_request = ApprovalRequest.objects.get(
                approval_request_ref=request_id
            )

            try:
                self._update_approval_request()
                self._update_progress_message()

                if (
                    self.approval_request.state
                    == ApprovalRequest.State.APPROVED
                ):
                    StartOrder(self.approval_request.order).process()
                elif self.approval_request.state in [
                    ApprovalRequest.State.CANCELED,
                    ApprovalRequest.State.FAILED,
                    ApprovalRequest.State.DENIED,
                ]:
                    FinishOrder(self.approval_request.order).process(
                        is_complete=False
                    )

            except Exception as error:
                order = self.approval_request.order
                order.mark_failed(
                    gettext_noop(
                        "Internal Error. Please contact our support team."
                    )
                )
                raise error
        except Exception as error:
            logger.error(
                "Error processing approval event %s: %s",
                self.event,
                str(error),
            )
            raise error

        return self

    def _update_approval_request(self):
        if self.event == self.EVENT_REQUEST_FINISHED:
            state = self.payload["decision"]
            if state == "error":
                state = ApprovalRequest.State.FAILED
        elif self.event == self.EVENT_REQUEST_CANCELED:
            state = ApprovalRequest.State.CANCELED

        self.approval_request.state = state
        self.approval_request.reason = self.payload["reason"]
        self.approval_request.request_completed_at = timezone.now()
        self.approval_request.save()

    def _update_progress_message(self):
        approval_reason = self.approval_request.reason
        state = self.approval_request.state

        if approval_reason is None:
            message = gettext_noop(
                "Approval Request finished with status %(state)s"
            )
            params = {"state": state}
            logger.info("Approval Request finished with status %s", state)
        else:
            message = gettext_noop(
                "Approval Request finished with status %(state)s \
and reason %(reason)s"
            )
            params = {"state": state, "reason": approval_reason}

            logger.info(
                "Approval Request finished with status %s and reason %s",
                state,
                approval_reason,
            )

        self.approval_request.order.update_message(
            ProgressMessage.Level.INFO, message=message, params=params
        )
