""" Create an approval request """
import django_rq
import logging
from main.approval.models import Request, RequestContext
from main.approval.tasks import start_request_task

logger = logging.getLogger("approval")


class CreateRequest:
    """Create an approval request"""

    def __init__(self, data):
        self.data = data
        self.request = None
        self.job = None

    def process(self):
        # TODO: find workflow based on tags
        tag_resources = self.data.pop("tag_resources", None)

        content = self.data.pop("content")
        request_context = RequestContext.objects.create(
            content=content, context={}
        )
        self.request = Request.objects.create(
            request_context=request_context, **self.data
        )
        self.job = django_rq.enqueue(start_request_task, self.request.id)
        logger.info(
            "Enqueued job {} for request {}".format(
                self.job.id, self.request.id
            )
        )
        return self
