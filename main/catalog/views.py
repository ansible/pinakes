""" Default views for Catalog."""
import logging
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework.response import Response
from rest_framework import status

from common.tag_mixin import TagMixin
from common.image_mixin import ImageMixin
from common.queryset_mixin import QuerySetMixin

from main.models import Tenant
from main.catalog.models import (
    ApprovalRequest,
    Order,
    OrderItem,
    Portfolio,
    PortfolioItem,
    ProgressMessage,
)
from main.catalog.serializers import (
    ApprovalRequestSerializer,
    OrderItemSerializer,
    OrderSerializer,
    PortfolioItemSerializer,
    PortfolioSerializer,
    ProgressMessageSerializer,
    TenantSerializer,
)
from main.catalog.services.collect_tag_resources import CollectTagResources
from main.catalog.services.submit_approval_request import SubmitApprovalRequest
from main.catalog.services.start_order import StartOrder

# Create your views here.

logger = logging.getLogger("catalog")


class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for listing and creating tenants."""

    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ("id",)
    filter_fields = "__all__"


class PortfolioViewSet(
    ImageMixin,
    TagMixin,
    NestedViewSetMixin,
    QuerySetMixin,
    viewsets.ModelViewSet,
):
    """API endpoint for listing and creating portfolios."""

    serializer_class = PortfolioSerializer
    http_method_names = ["get", "post", "head", "patch", "delete"]
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filter_fields = ("name", "description", "created_at", "updated_at")


class PortfolioItemViewSet(
    ImageMixin,
    TagMixin,
    NestedViewSetMixin,
    QuerySetMixin,
    viewsets.ModelViewSet,
):
    """API endpoint for listing and creating portfolio items."""

    serializer_class = PortfolioItemSerializer
    http_method_names = ["get", "post", "head", "patch", "delete"]
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filter_fields = (
        "name",
        "description",
        "service_offering_ref",
        "portfolio",
        "created_at",
        "updated_at",
    )
    parent_field_name = "portfolio"
    parent_lookup_key = "parent_lookup_portfolio"


class OrderViewSet(NestedViewSetMixin, QuerySetMixin, viewsets.ModelViewSet):
    """API endpoint for listing and creating orders."""

    serializer_class = OrderSerializer
    http_method_names = ["get", "post", "head", "delete"]
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filter_fields = (
        "state",
        "order_request_sent_at",
        "created_at",
        "updated_at",
        "completed_at",
    )

    @action(methods=["post"], detail=True)
    def submit(self, request, pk):
        """Orders the specified pk order."""
        order = get_object_or_404(Order, pk=pk)

        tag_resources = CollectTagResources(order).process().tag_resources
        message = _("Computed tags for order {}: {}").format(
            order.id, tag_resources
        )
        order.update_message(ProgressMessage.Level.INFO, message)

        logger.info("Creating approval request for order id %d", order.id)
        SubmitApprovalRequest(tag_resources, order).process()

        return Response(status=status.HTTP_204_NO_CONTENT)

    # TODO:
    @action(methods=["patch"], detail=True)
    def cancel(self, request, pk):
        """Cancels the specified pk order."""
        pass


class OrderItemViewSet(
    NestedViewSetMixin, QuerySetMixin, viewsets.ModelViewSet
):
    """API endpoint for listing and creating order items."""

    serializer_class = OrderItemSerializer
    http_method_names = ["get", "post", "head", "delete"]
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filter_fields = (
        "name",
        "count",
        "state",
        "portfolio_item",
        "order",
        "external_url",
        "order_request_sent_at",
        "created_at",
        "updated_at",
        "completed_at",
    )
    parent_field_name = "order"
    parent_lookup_key = "parent_lookup_order"


class ApprovalRequestViewSet(
    NestedViewSetMixin, QuerySetMixin, viewsets.ModelViewSet
):
    """API endpoint for listing approval requests."""

    queryset = ApprovalRequest.objects.all()
    serializer_class = ApprovalRequestSerializer
    http_method_names = ["get"]
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filter_fields = (
        "order",
        "approval_request_ref",
        "state",
        "reason",
        "request_completed_at",
        "created_at",
        "updated_at",
    )
    parent_field_name = "order"
    parent_lookup_key = "parent_lookup_order"

    def list(self, request, *args, **kwargs):
        order_id = kwargs.pop(self.parent_lookup_key)
        approval_request = ApprovalRequest.objects.get(order_id=order_id)

        serializer = self.get_serializer(approval_request)
        return Response(serializer.data)


class ProgressMessageViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """API endpoint for listing progress messages."""

    serializer_class = ProgressMessageSerializer
    http_method_names = ["get"]
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filter_fields = (
        "received_at",
        "messageable_id",
        "messageable_type",
        "level",
        "created_at",
        "updated_at",
    )

    def get_queryset(self):
        """return queryset based on messageable_type"""

        parent_type = self.request.path.split("/")[3]
        messageable_id = self.kwargs.get("parent_lookup_messageable_id")

        messageable_type = "Order" if parent_type == "orders" else "OrderItem"

        return ProgressMessage.objects.filter(
            tenant=Tenant.current(),
            messageable_type=messageable_type,
            messageable_id=messageable_id,
        )
