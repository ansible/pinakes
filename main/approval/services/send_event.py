""" Send an event when a request changes it state """
import logging

from main.catalog.services.receive_approval_events import ReceiveApprovalEvents


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
        getattr(self, f"_SendEvent__{self.event}")()
        return self

    def __request_started(self):
        return self.__send_event({"request_id": self.subject.id})

    def __request_finished(self):
        return self.__send_event(
            {
                "request_id": self.subject.id,
                "decision": self.subject.decision,
                "reason": self.subject.reason,
            }
        )

    def __request_canceled(self):
        return self.__send_event(
            {"request_id": self.subject.id, "reason": self.subject.reason}
        )

    def __workflow_deleted(self):
        # subject is workflow_id
        return self.__send_event({"workflow_id": self.subject})

    def __send_event(self, payload):
        logger.info(
            "Sending event {} with payload({})".format(self.event, payload)
        )
        ReceiveApprovalEvents(
            event=self.event,
            payload=payload,
        ).process()
