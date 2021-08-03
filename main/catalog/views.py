""" Default views for Catalog."""
import logging

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework.response import Response
from rest_framework import status

from common.tag_mixin import TagMixin
from main.models import Tenant
from main.catalog.models import (
    Portfolio,
    PortfolioItem,
    Order,
    OrderItem
)
from main.catalog.serializers import (
    TenantSerializer,
    PortfolioSerializer,
    PortfolioItemSerializer,
    OrderSerializer,
    OrderItemSerializer
)

from main.catalog.services.start_order_item import StartOrderItem
# Create your views here.

logger = logging.getLogger("catalog")

class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for listing and creating tenants."""

    queryset = Tenant.objects.all().order_by("id")
    serializer_class = TenantSerializer
    permission_classes = (IsAuthenticated,)


class PortfolioViewSet(TagMixin, NestedViewSetMixin, viewsets.ModelViewSet):
    """API endpoint for listing and creating portfolios."""

    queryset = Portfolio.objects.all().order_by("created_at")
    serializer_class = PortfolioSerializer
    http_method_names = ["get", "post", "head", "patch", "delete"]
    permission_classes = (IsAuthenticated,)


class PortfolioItemViewSet(TagMixin, NestedViewSetMixin, viewsets.ModelViewSet):
    """API endpoint for listing and creating portfolio items."""

    queryset = PortfolioItem.objects.all()
    serializer_class = PortfolioItemSerializer
    http_method_names = ["get", "post", "head", "patch", "delete"]
    permission_classes = (IsAuthenticated,)


class OrderViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """API endpoint for listing and creating orders."""

    queryset = Order.objects.all().order_by("created_at")
    serializer_class = OrderSerializer
    http_method_names = ["get", "post", "head", "delete"]
    permission_classes = (IsAuthenticated,)

    # TODO: Add Approval Hook, handle multiple order items
    @action(methods=["post"], detail=True)
    def submit(self, request, pk):
        """Orders the specified pk order."""
        order_item = OrderItem.objects.filter(order_id=pk).first()
        if order_item is None:
           return Response({'status': 'details'}, status=status.HTTP_404_NOT_FOUND)

        StartOrderItem(order_item).process()
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    # TODO:
    @action(methods=["patch"], detail=True)
    def cancel(self, request, pk):
        """Cancels the specified pk order."""
        pass


class OrderItemViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """API endpoint for listing and creating order items."""

    queryset = OrderItem.objects.all().order_by("created_at")
    serializer_class = OrderItemSerializer
    http_method_names = ["get", "post", "head", "delete"]
    permission_classes = (IsAuthenticated,)
