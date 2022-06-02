"""Create a request to Approval"""
import logging
import traceback

from django.utils.translation import gettext_lazy as _

from pinakes.main.approval.services.create_request import (
    CreateRequest,
)
from pinakes.main.catalog.exceptions import (
    BadParamsException,
)
from pinakes.main.catalog.models import ApprovalRequest
from pinakes.main.models import Source

logger = logging.getLogger("catalog")


class SubmitApprovalRequest:
    """Submit a new approval request"""

    def __init__(self, tag_resources, order, context=None):
        self.tag_resources = tag_resources
        self.order = order
        self.order_item = order.product
        if context is None:
            context = {}
        self.context = context

    def process(self):
        self.order.mark_approval_pending()
        self._submit_approval_request()

        return self

    def _submit_approval_request(self):
        try:
            request_body = self._create_approval_request_body()
            svc = CreateRequest(request_body, self.context).process()

            ApprovalRequest.objects.create(
                approval_request_ref=str(svc.request.id),
                state=str(svc.request.decision),
                order=self.order,
                tenant_id=self.order.tenant_id,
            )

            logger.info(
                "Approval Requests Submitted for Order %d", self.order.id
            )

        except Exception as error:
            logger.error(
                "Failed to submit request to approval for Order %d, error: %s",
                self.order.id,
                error,
            )
            logger.error(traceback.format_exc())
            raise BadParamsException(
                _(
                    "Failed to submit request to approval for Order {},"
                    " error: {}"
                ).format(
                    self.order.id,
                    str(error),
                )
            )

    def _create_approval_request_body(self):
        return {
            "name": self.order_item.portfolio_item.name,
            "content": {
                "product": self.order_item.portfolio_item.name,
                "portfolio": self.order_item.portfolio_item.portfolio.name,
                "order_id": str(self.order.id),
                "platform": self._platform(),
                "params": self.order_item.service_parameters,
            },
            "tag_resources": self.tag_resources,
            "tenant_id": self.order.tenant_id,
            "user_id": self.order.user_id,
        }

    def _platform(self):
        source_ref = self.order_item.portfolio_item.service_offering_source_ref
        if not source_ref:
            logger.warning(
                "Portfolio item %d has no related platform information",
                self.order_item.portfolio_item.id,
            )
            return ""

        obj = Source.objects.filter(id=int(source_ref)).first()

        if obj:
            return obj.name
        else:
            logger.warning("Source %s is not available", source_ref)
            return ""
