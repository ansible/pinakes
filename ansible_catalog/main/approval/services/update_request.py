"""Update a request"""

from ansible_catalog.main.approval.models import Request


class UpdateRequest:
    """Service class to update a request"""

    def __init__(self, request, options):
        self.request = (
            request
            if isinstance(request, Request)
            else Request.objects.get(id=request)
        )
        self.options = options

    def process(self):
        return self
