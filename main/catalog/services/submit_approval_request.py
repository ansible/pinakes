""" Create a request to Approval """
import logging
from django.utils.translation import gettext_lazy as _

from main.approval.services.create_request import (
    CreateRequest,
)
from main.catalog.models import ApprovalRequest
from main.models import Source

logger = logging.getLogger("catalog")


class SubmitApprovalRequest:
    """Submit a new approval request"""

    def __init__(self, tag_resources, order):
        self.tag_resources = tag_resources
        self.order = order
        self.order_item = order.product

    def process(self):
        self.order.mark_approval_pending()
        self.submit_approval_request()

        return self

    def submit_approval_request(self):
        try:
            request_body = self.__create_approval_request_body()
            svc = CreateRequest(request_body).process()

            ApprovalRequest.objects.create(
                approval_request_ref=str(svc.request.id),
                state=str(svc.request.decision),
                order=self.order,
                tenant_id=self.order.tenant_id,
            )

            logger.info(
                f"Approval Requests Submitted for Order {self.order.id}"
            )

        except Exception as error:
            logger.error(
                f"Failed to submit request to approval for Order {self.order.id}, error: {error}"
            )
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
            "tenant_id": self.order.tenant_id,
        }

    def __platform(self):
        source_ref = self.order_item.portfolio_item.service_offering_source_ref
        obj = Source.objects.get(id=int(source_ref))

        return obj.name if obj is not None else ""
