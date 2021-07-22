import logging

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from rest_framework_extensions.mixins import NestedViewSetMixin

from common.tag_mixin import TagMixin
from inventory.basemodel import Source
from inventory.models import (
    ServiceInventory,
    ServiceOffering,
    ServiceOfferingNode,
    ServicePlan
)
from inventory.serializers import (
    ServiceInventorySerializer,
    ServicePlanSerializer,
    ServiceOfferingSerializer,
    ServiceOfferingNodeSerializer,
    SourceSerializer
)
from inventory.task_utils.refresh_inventory import RefreshInventory

# Create your views here.
logger = logging.getLogger("inventory")

class SourceViewSet(NestedViewSetMixin, ModelViewSet):
    """API endpoint for listing and updating sources."""

    queryset = Source.objects.all().order_by("created_at")
    serializer_class = SourceSerializer
    permission_classes = (IsAuthenticated,)

    # Enable PATCH for refresh API
    http_method_names = ["get", "patch", "head"]

    @action(methods=["patch"], detail=True)
    def refresh(self, request, pk):
        source = get_object_or_404(Source, pk=pk)
        RefreshInventory(source.tenant_id, source.id).process()

        return Response(None, status=status.HTTP_204_NO_CONTENT)

class ServicePlanViewSet(NestedViewSetMixin, ModelViewSet):
    """API endpoint for listing and retrieving service plans."""

    queryset = ServicePlan.objects.all().order_by("created_at")
    serializer_class = ServicePlanSerializer
    permission_classes = (IsAuthenticated,)

    http_method_names = ["get", "head"]

class ServiceOfferingViewSet(NestedViewSetMixin, ModelViewSet):
    """API endpoint for listing and retrieving service offerings."""

    queryset = ServiceOffering.objects.all().order_by("created_at")
    serializer_class = ServiceOfferingSerializer
    permission_classes = (IsAuthenticated,)

    http_method_names = ["get", "head"]

    # TODO:
    @action(methods=["post"], detail=True)
    def applied_inventories_tags(self, request, pk):
        return Response(status=status.HTTP_204_NO_CONTENT)

    # TODO:
    @action(methods=["post"], detail=True)
    def order(self, request, pk):
        return Response(status=status.HTTP_204_NO_CONTENT)

class ServiceInventoryViewSet(TagMixin, NestedViewSetMixin, ModelViewSet):
    """API endpoint for listing and creating service inventories."""

    queryset = ServiceInventory.objects.all().order_by("created_at")
    serializer_class = ServiceInventorySerializer
    permission_classes = (IsAuthenticated,)

    # For tagging purpose, enable POST action here
    http_method_names = ["get", "post", "head"]
