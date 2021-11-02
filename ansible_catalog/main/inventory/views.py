import logging

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from rest_framework_extensions.mixins import NestedViewSetMixin
import django_rq

from ansible_catalog.common.tag_mixin import TagMixin
from ansible_catalog.common.queryset_mixin import QuerySetMixin
from ansible_catalog.main.models import Source
from ansible_catalog.main.inventory.models import (
    ServiceInventory,
    ServiceOffering,
    ServicePlan,
)
from ansible_catalog.main.inventory.serializers import (
    ServiceInstanceSerializer,
    ServiceInventorySerializer,
    ServicePlanSerializer,
    ServiceOfferingSerializer,
    SourceSerializer,
)
from ansible_catalog.main.inventory.tasks import refresh_task

# Create your views here.
logger = logging.getLogger("inventory")


class SourceViewSet(NestedViewSetMixin, QuerySetMixin, ModelViewSet):
    """API endpoint for listing and updating sources."""

    serializer_class = SourceSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filterset_fields = ("name",)
    search_fields = ("name",)

    # Enable PATCH for refresh API
    http_method_names = ["get", "patch", "head"]

    @action(methods=["patch"], detail=True)
    def refresh(self, request, pk):
        source = get_object_or_404(Source, pk=pk)
        result = django_rq.enqueue(refresh_task, source.tenant_id, source.id)
        logger.info("Job Id is %s", result.id)

        return Response(None, status=status.HTTP_204_NO_CONTENT)


class ServicePlanViewSet(NestedViewSetMixin, QuerySetMixin, ModelViewSet):
    """API endpoint for listing and retrieving service plans."""

    serializer_class = ServicePlanSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filterset_fields = (
        "name",
        "service_offering",
    )
    search_fields = ("name",)
    parent_field_names = (
        "service_offering",
        "source",
    )  # do not modify the sequence
    http_method_names = ["get", "head"]


class ServiceOfferingViewSet(NestedViewSetMixin, QuerySetMixin, ModelViewSet):
    """API endpoint for listing and retrieving service offerings."""

    serializer_class = ServiceOfferingSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filterset_fields = (
        "name",
        "description",
        "survey_enabled",
        "kind",
        "service_inventory",
    )
    search_fields = ("name", "description")
    parent_field_names = ("source",)
    http_method_names = ["get", "head"]

    # TODO:
    @action(methods=["post"], detail=True)
    def applied_inventories_tags(self, request, pk):
        return Response(status=status.HTTP_204_NO_CONTENT)

    # TODO:
    @action(methods=["post"], detail=True)
    def order(self, request, pk):
        return Response(status=status.HTTP_204_NO_CONTENT)


class ServiceInventoryViewSet(
    TagMixin, NestedViewSetMixin, QuerySetMixin, ModelViewSet
):
    """API endpoint for listing and creating service inventories."""

    serializer_class = ServiceInventorySerializer
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filterset_fields = (
        "description",
        "source_ref",
        "source_created_at",
        "source_updated_at",
        "created_at",
        "updated_at",
    )
    search_fields = ("description",)
    parent_field_names = ("source",)

    # For tagging purpose, enable POST action here
    http_method_names = ["get", "post", "head"]


class ServiceInstanceViewSet(QuerySetMixin, ModelViewSet):
    """API endpoint for listing service instances."""

    serializer_class = ServiceInstanceSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filterset_fields = (
        "name",
        "source_ref",
        "source_created_at",
        "source_updated_at",
        "created_at",
        "updated_at",
    )
    search_fields = ("name",)

    http_method_names = ["get", "head"]
