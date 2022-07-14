import logging

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from rest_framework_extensions.mixins import NestedViewSetMixin
import rq.job as rq_job
import django_rq

from pinakes.common.tag_mixin import TagMixin
from pinakes.common.queryset_mixin import QuerySetMixin
from pinakes.common.serializers import TaskSerializer
from pinakes.main.models import Source
from pinakes.main.inventory.exceptions import (
    RefreshAlreadyRegisteredException,
)
from pinakes.main.inventory.serializers import (
    InventoryServicePlanSerializer,
    ServiceInstanceSerializer,
    ServiceInventorySerializer,
    ServiceOfferingSerializer,
    SourceSerializer,
)
from pinakes.main.inventory.tasks import refresh_task
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
)

# Create your views here.
logger = logging.getLogger("inventory")


@extend_schema_view(
    retrieve=extend_schema(
        description="Get an existing source",
    ),
    list=extend_schema(
        description="List all sources",
    ),
    partial_update=extend_schema(
        description="Edit an existing source",
    ),
)
class SourceViewSet(NestedViewSetMixin, QuerySetMixin, ModelViewSet):
    """API endpoint for listing and updating sources."""

    serializer_class = SourceSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filterset_fields = ("name",)
    search_fields = ("name",)

    # Enable PATCH for refresh API
    http_method_names = ["get", "patch", "head"]

    @extend_schema(
        description=(
            "Refresh an existing Source. It returns a background task id"
        ),
        request=None,
        responses={status.HTTP_202_ACCEPTED: TaskSerializer},
    )
    @action(methods=["patch"], detail=True)
    def refresh(self, request, pk):
        source = get_object_or_404(Source, pk=pk)

        if source.last_refresh_task_ref:
            try:
                job = rq_job.Job.fetch(
                    source.last_refresh_task_ref,
                    connection=django_rq.get_connection(),
                )
                job_status = job.get_status(refresh=True)

                if job_status in ["queued", "started"]:
                    logger.info(
                        "Refresh job %s is already %s, please try again later",
                        source.last_refresh_task_ref,
                        job_status,
                    )
                    raise RefreshAlreadyRegisteredException(
                        _(
                            "Refresh job {} is already {}, please try again"
                            " later"
                        ).format(
                            source.last_refresh_task_ref,
                            job_status,
                        )
                    )

            except rq_job.NoSuchJobError:
                logger.info(
                    "Refresh job %s not found, run refresh again",
                    source.last_refresh_task_ref,
                )

        result = django_rq.enqueue(refresh_task, source.tenant_id, source.id)
        logger.info("Refresh job id is %s", result.id)

        source.last_refresh_task_ref = result.id
        source.save()

        serializer = TaskSerializer(result)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


@extend_schema_view(
    retrieve=extend_schema(
        description="Get an existing inventory service plan",
    ),
    list=extend_schema(
        description="List all inventory service plans",
    ),
)
class InventoryServicePlanViewSet(
    NestedViewSetMixin, QuerySetMixin, ModelViewSet
):
    """API endpoint for listing and retrieving service plans."""

    serializer_class = InventoryServicePlanSerializer
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


@extend_schema_view(
    retrieve=extend_schema(
        description="Get an existing service offering",
    ),
    list=extend_schema(
        description="List all service offerings",
    ),
)
class ServiceOfferingViewSet(NestedViewSetMixin, QuerySetMixin, ModelViewSet):
    """API endpoint for listing and retrieving service offerings."""

    serializer_class = ServiceOfferingSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filterset_fields = (
        "name",
        "description",
        "survey_enabled",
        "service_inventory",
    )
    search_fields = ("name", "description")
    parent_field_names = ("source",)
    http_method_names = ["get", "head"]


@extend_schema_view(
    retrieve=extend_schema(
        description="Get an existing inventory",
    ),
    list=extend_schema(
        description="List all service inventories",
    ),
)
class ServiceInventoryViewSet(
    TagMixin, NestedViewSetMixin, QuerySetMixin, ModelViewSet
):
    """API endpoint for listing and creating service inventories."""

    serializer_class = ServiceInventorySerializer
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filterset_fields = (
        "name",
        "description",
        "source_ref",
        "source_created_at",
        "source_updated_at",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "name",
        "description",
    )
    parent_field_names = ("source",)

    # For tagging purpose, enable POST action here
    http_method_names = ["get", "post", "head"]


@extend_schema_view(
    retrieve=extend_schema(
        description="Get an existing service instance",
    ),
    list=extend_schema(
        description="List all service instances",
    ),
)
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
