""" Default views for Approval."""
import logging

from decimal import Decimal
from rest_framework.decorators import action
from rest_framework import viewsets, status, exceptions
from rest_framework.response import Response
from rest_framework.filters import (
    BaseFilterBackend,
    OrderingFilter,
    SearchFilter,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework_extensions.mixins import NestedViewSetMixin
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from ansible_catalog.main.models import Tenant
from ansible_catalog.main.approval.models import (
    Template,
    Workflow,
    Request,
)
from ansible_catalog.main.approval.serializers import (
    TemplateSerializer,
    WorkflowSerializer,
    RequestSerializer,
    RequestInSerializer,
    RequestCompleteSerializer,
    ActionSerializer,
    ResourceObjectSerializer,
)
from ansible_catalog.main.approval.services.link_workflow import LinkWorkflow
from ansible_catalog.main.approval.exceptions import InsufficientParamsException
from ansible_catalog.common.queryset_mixin import QuerySetMixin

logger = logging.getLogger("approval")


class TemplateViewSet(
    NestedViewSetMixin, QuerySetMixin, viewsets.ModelViewSet
):
    """API endpoint for listing and templates."""

    http_method_names = ["get", "head"]
    permission_classes = (IsAuthenticated,)
    serializer_class = TemplateSerializer
    ordering_fields = "__all__"  # This line is optional, default
    ordering = ("-id",)
    search_fields = ("title", "description")


class WorkflowFilterBackend(BaseFilterBackend):
    """
    Filter that selects workflows assigned to external resource.
    """

    def filter_queryset(self, request, queryset, _view):
        resource_params = {
            "app_name": request.query_params.get("app_name", None),
            "object_type": request.query_params.get("object_type", None),
            "object_id": request.query_params.get("object_id"),
        }
        num_of_nones = list(resource_params.values()).count(None)

        # Normal list workflows operation
        if num_of_nones == 3:
            return queryset
        # List workflows by query parameters
        elif num_of_nones == 0:
            workflow_ids = (
                LinkWorkflow(None, resource_params)
                .process(LinkWorkflow.Operation.FIND)
                .workflow_ids
            )
            return queryset.filter(id__in=workflow_ids)

        logger.error(
            "Insufficient resource object params: %s", resource_params
        )
        raise InsufficientParamsException(
            "Insufficient resource object params: {}".format(resource_params)
        )


class WorkflowViewSet(
    NestedViewSetMixin, QuerySetMixin, viewsets.ModelViewSet
):
    """API endpoint for listing, creating, and updating workflows."""

    serializer_class = WorkflowSerializer
    http_method_names = ["get", "post", "head", "patch", "delete"]
    permission_classes = (IsAuthenticated,)
    filter_backends = (
        WorkflowFilterBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    )
    filterset_fields = (
        "name",
        "description",
        "template",
        "created_at",
        "updated_at",
    )
    search_fields = ("name", "description")
    parent_field_name = "template"
    parent_lookup_key = "parent_lookup_template"
    queryset_order_by = "internal_sequence"

    @extend_schema(
        request=ResourceObjectSerializer,
        responses={204: None},
    )
    @action(methods=["post"], detail=True)
    def link(self, request, pk):
        workflow = get_object_or_404(Workflow, pk=pk)

        LinkWorkflow(workflow, request.data).process(
            LinkWorkflow.Operation.ADD
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        request=ResourceObjectSerializer,
        responses={204: None},
    )
    @action(methods=["post"], detail=True)
    def unlink(self, request, pk):
        workflow = get_object_or_404(Workflow, pk=pk)

        LinkWorkflow(workflow, request.data).process(
            LinkWorkflow.Operation.REMOVE
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        max_obj = (
            Workflow.objects.filter(tenant=Tenant.current())
            .order_by("-internal_sequence")
            .first()
        )
        if max_obj is None:
            next_seq = Decimal(1)
        else:
            next_seq = Decimal(
                max_obj.internal_sequence.to_integral_value() + 1
            )
        serializer.save(
            template=Template(id=self.kwargs[self.parent_lookup_key]),
            internal_sequence=next_seq,
            tenant=Tenant.current(),
        )


class RequestViewSet(NestedViewSetMixin, QuerySetMixin, viewsets.ModelViewSet):
    """API endpoint for listing and creating requests"""

    serializer_class = RequestSerializer
    http_method_names = ["get", "post"]
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filterset_fields = "__all__"
    search_fields = ("name", "description", "state", "decision", "reason")
    parent_field_name = "parent"
    parent_lookup_key = "parent_lookup_parent"

    @extend_schema(
        request=RequestInSerializer,
        responses={201: RequestSerializer},
    )
    def create(self, request, *args, **kwargs):
        serializer = RequestInSerializer(data=request.data)
        output_serializer = serializer  # default
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            output_serializer = RequestSerializer(
                serializer.save(
                    tenant=Tenant.current(), user=self.request.user
                )
            )
        except Exception as error:
            raise exceptions.APIException(error) from error # 500 internal error
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        responses={200: RequestCompleteSerializer},
    )
    @action(methods=["get"], detail=True)
    def full(self, request, pk):
        """Details of a request with its sub_requests and actions"""
        instance = self.get_object()
        serializer = RequestCompleteSerializer(instance)
        return Response(serializer.data)


class ActionViewSet(QuerySetMixin, viewsets.ModelViewSet):
    """API endpoint for listing and creating actions"""

    serializer_class = ActionSerializer
    http_method_names = ["get", "post"]
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filterset_fields = "__all__"
    search_fields = ("operation", "comments")
    parent_field_name = "request"
    parent_lookup_key = "parent_lookup_request"

    def perform_create(self, serializer):
        serializer.save(
            request=Request(id=self.kwargs[self.parent_lookup_key]),
            user=self.request.user,
            tenant=Tenant.current(),
        )
