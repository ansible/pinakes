""" Create an approval request """
import logging
import threading
from os import getenv
from time import sleep

from main.approval.models import Request, RequestContext
from .send_event import SendEvent


logger = logging.getLogger("approval")


class CreateRequest:
    """Create an approval request"""

    def __init__(self, data):
        self.data = data
        self.request = None
        try:
            self.__auto_interval = float(getenv("AUTO_APPROVAL_INTERVAL"))
        except:
            self.__auto_interval = 0.5

    def process(self):
        content = self.data.pop("content")
        request_context = RequestContext.objects.create(
            content=content, context={}
        )
        self.request = Request.objects.create(
            request_context=request_context, **self.data
        )
        self.__prepare_request()
        return self

    def __prepare_request(self):
        try:
            threading.Thread(target=self.__start_request).start()
        except:
            logger.error(
                f"Failed to start a thread to execute request (id={self.request.id})"
            )

    def __start_request(self):
        sleep(self.__auto_interval)
        SendEvent(self.request, SendEvent.EVENT_REQUEST_STARTED).process()
        self.request.state = Request.State.COMPLETED
        self.request.decision = Request.Decision.APPROVED
        self.request.save()
        SendEvent(self.request, SendEvent.EVENT_REQUEST_FINISHED).process()
