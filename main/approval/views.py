""" Default views for Approval."""
import logging

from decimal import Decimal
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_extensions.mixins import NestedViewSetMixin
from django.core.exceptions import ValidationError

from main.models import Tenant
from main.approval.models import (
    Template,
    Workflow,
    Request,
    Action,
)
from main.approval.serializers import (
    TemplateSerializer,
    WorkflowSerializer,
    RequestSerializer,
    RequestInSerializer,
    RequestCompleteSerializer,
    ActionSerializer,
)
from common.queryset_mixin import QuerySetMixin

logger = logging.getLogger("approval")

class TemplateViewSet(NestedViewSetMixin, QuerySetMixin, viewsets.ModelViewSet):
    """API endpoint for listing and templates."""

    http_method_names = ["get", "head"]
    permission_classes = (IsAuthenticated,)
    serializer_class = TemplateSerializer
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = "__all__" # This line is optional, default
    ordering = ("-id",)


class WorkflowViewSet(NestedViewSetMixin, QuerySetMixin, viewsets.ModelViewSet):
    """API endpoint for listing, creating, and updating workflows."""

    serializer_class = WorkflowSerializer
    http_method_names = ["get", "post", "head", "patch", "delete"]
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.OrderingFilter,)
    parent_field_name = "template"
    parent_lookup_key = "parent_lookup_template"
    queryset_order_by = "internal_sequence"

    def perform_create(self, serializer):
        max_obj = Workflow.objects.filter(tenant=Tenant.current()).order_by('-internal_sequence').first()
        if max_obj is None:
            next_seq = Decimal(1)
        else:
            next_seq = Decimal(max_obj.internal_sequence.to_integral_value() + 1)
        serializer.save(
            template=Template(id=self.kwargs["parent_lookup_template"]),
            internal_sequence=next_seq,
            tenant=Tenant.current()
        )


class RequestViewSet(NestedViewSetMixin, QuerySetMixin, viewsets.ModelViewSet):
    """API endpoint for listing and creating requests"""

    serializer_class = RequestSerializer
    http_method_names = ["get", "post"]
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.OrderingFilter,)
    ordering = ("-id",)
    parent_field_name = "parent"
    parent_lookup_key = "parent_lookup_parent"

    def create(self, request, *args, **kwargs):
        serializer = RequestInSerializer(data=request.data)
        output_serializer = serializer # default
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST)
        try:
            output_serializer = RequestSerializer(
                serializer.save(tenant=Tenant.current(), user=self.request.user)
            )
        except Exception as error:
            raise ValidationError({"detail": error}) from error
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

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
    filter_backends = (filters.OrderingFilter,)
    ordering = ("-id",)
    parent_field_name = "request"
    parent_lookup_key = "parent_lookup_request"

    def perform_create(self, serializer):
        serializer.save(
            request=Request(id=self.kwargs["parent_lookup_request"]),
            user=self.request.user,
            tenant=Tenant.current()
        )
