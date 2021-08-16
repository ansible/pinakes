""" Create a request to Approval """
from main.approval.models import Request, RequestContext


class CreateApprovalRequest:
    """Create a new approval request"""

    def __init__(self, request_body):
        self.request_body = request_body
        self.request = None

    def process(self):
        self.create_approval_request()

        return self

    def create_approval_request(self):
        content = self.request_body.pop("content", None)
        request_context = (
            RequestContext.objects.create(content=content, context={})
            if content is not None
            else None
        )

        # find workflow
        tag_resources = self.request_body.pop("tag_resources", None)
        if tag_resources is not None:
            pass

        self.request = Request.objects.create(
            request_context=request_context, **self.request_body
        )
