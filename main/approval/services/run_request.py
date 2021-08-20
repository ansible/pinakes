"""Execute a request"""
from main.approval.models import Request
from .send_event import SendEvent


class RunRequest:
    """Execute a request"""

    def __init__(self, request_id):
        self.request = Request.objects.get(pk=request_id)

    def process(self):
        SendEvent(self.request, SendEvent.EVENT_REQUEST_STARTED).process()
        self.request.state = Request.State.COMPLETED
        self.request.decision = Request.Decision.APPROVED
        self.request.reason = "Auto Approved"
        self.request.save()
        SendEvent(self.request, SendEvent.EVENT_REQUEST_FINISHED).process()
        return self
