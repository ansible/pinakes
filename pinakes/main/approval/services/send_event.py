"""Send an event when a request changes it state"""
import logging

from pinakes.main.catalog.services.handle_approval_events import (
    HandleApprovalEvents,
)


logger = logging.getLogger("approval")


class SendEvent:
    """SendEvent service class"""

    EVENT_REQUEST_STARTED = "request_started"
    EVENT_REQUEST_FINISHED = "request_finished"
    EVENT_REQUEST_CANCELED = "request_canceled"
    EVENT_WORKFLOW_DELETED = "workflow_deleted"

    def __init__(self, subject, event):
        """subject is either a request or workflow_id"""
        self.subject = subject
        self.event = event

    def process(self):
        getattr(self, f"_{self.event}")()
        return self

    def _request_started(self):
        return self._send_event({"request_id": self.subject.id})

    def _request_finished(self):
        return self._send_event(
            {
                "request_id": self.subject.id,
                "decision": self.subject.decision,
                "reason": self.subject.reason,
            }
        )

    def _request_canceled(self):
        return self._send_event(
            {"request_id": self.subject.id, "reason": self.subject.reason}
        )

    def _workflow_deleted(self):
        # subject is workflow_id
        return self._send_event({"workflow_id": self.subject})

    def _send_event(self, payload):
        logger.info("Sending event %s with payload(%s)", self.event, payload)
        HandleApprovalEvents(
            event=self.event,
            payload=payload,
        ).process()
