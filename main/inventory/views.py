import logging

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from rest_framework_extensions.mixins import NestedViewSetMixin
import django_rq

from common.tag_mixin import TagMixin
from main.models import Source
from main.inventory.models import (
    ServiceInventory,
    ServiceOffering,
    ServiceOfferingNode,
    ServicePlan
)
from main.inventory.serializers import (
    ServiceInventorySerializer,
    ServicePlanSerializer,
    ServiceOfferingSerializer,
    ServiceOfferingNodeSerializer,
    SourceSerializer
)
from main.inventory.tasks import refresh_task

# Create your views here.
logger = logging.getLogger("inventory")


class SourceViewSet(NestedViewSetMixin, ModelViewSet):
    """API endpoint for listing and updating sources."""

    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filter_fields = ("name",)

    # Enable PATCH for refresh API
    http_method_names = ["get", "patch", "head"]

    @action(methods=["patch"], detail=True)
    def refresh(self, request, pk):
        source = get_object_or_404(Source, pk=pk)
        result = django_rq.enqueue(refresh_task, source.tenant_id, source.id)
        logger.info(f"Job Id is {result.id}")

        return Response(None, status=status.HTTP_204_NO_CONTENT)


class ServicePlanViewSet(NestedViewSetMixin, ModelViewSet):
    """API endpoint for listing and retrieving service plans."""

    queryset = ServicePlan.objects.all()
    serializer_class = ServicePlanSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filter_fields = ("name", "service_offering",)

    http_method_names = ["get", "head"]


class ServiceOfferingViewSet(NestedViewSetMixin, ModelViewSet):
    """API endpoint for listing and retrieving service offerings."""

    queryset = ServiceOffering.objects.all()
    serializer_class = ServiceOfferingSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filter_fields = (
        "name",
        "description",
        "survey_enabled",
        "kind",
        "service_inventory",
    )

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

    queryset = ServiceInventory.objects.all()
    serializer_class = ServiceInventorySerializer
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filter_fields = (
        "description",
        "source_ref",
        "source_created_at",
        "source_updated_at",
        "created_at",
        "updated_at",
    )

    # For tagging purpose, enable POST action here
    http_method_names = ["get", "post", "head"]
