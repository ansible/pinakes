""" Create a request to Approval """
import logging
from django.utils.translation import gettext_lazy as _

from main.approval.models import Request
from main.catalog.models import ApprovalRequest
from main.models import Source

logger = logging.getLogger("catalog")


class CreateApprovalRequest:
    """Create a new approval request"""

    def __init__(self, tag_resources, order_item):
        self.order_item = order_item
        self.tag_resources = tag_resources
        self.order = order_item.order

    def process(self):
        self.order.mark_approval_pending()
        self.submit_approval_request(self.order)

        return self

    def submit_approval_request(self, order):
        try:
            request_body = self.__create_approval_request_body()
            req = Request.objects.create(
                tenant_id=order.tenant_id, **request_body
            )

            ApprovalRequest.objects.create(
                approval_request_ref=req.id,
                state=str(req.decision),
                order_id=order.id,
                tenant_id=order.tenant_id,
            )

            logger.info(
                f"Approval Requests Submitted for Order {self.order.id}"
            )

        except Exception as error:
            raise error

    def __create_approval_request_body(self):
        return {
            "name": self.order_item.portfolio_item.name,
            "content": {
                "product": self.order_item.portfolio_item.name,
                "portfolio": self.order_item.portfolio_item.portfolio.name,
                "order_id": str(self.order.id),
                "platform": self.__platform(),
                "params": self.order_item.service_parameters,
            },
            "tag_resources": self.tag_resources,
        }

    def __platform(self):
        source_ref = self.order_item.portfolio_item.service_offering_source_ref
        source = Source.objects.filter(id=source_ref).first()

        return source.name if source is not None else ""
