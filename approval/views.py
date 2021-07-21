""" Default views for Approval."""
import logging
from decimal import Decimal
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_extensions.mixins import NestedViewSetMixin
from django.core.exceptions import ValidationError

from .basemodel import Tenant
from .models import (
    Template,
    Workflow,
    Request,
    Action,
)
from .serializers import (
    TemplateSerializer,
    WorkflowSerializer,
    RequestSerializer,
    RequestInSerializer,
    ActionSerializer,
)

logger = logging.getLogger("approval")

class TemplateViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """API endpoint for listing and templates."""

    http_method_names = ["get", "head"]
    permission_classes = (IsAuthenticated,)
    serializer_class = TemplateSerializer
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = "__all__" # This line is optional, default
    ordering = ("-id",)

    def get_queryset(self):
        return Template.objects.filter(tenant=Tenant.current())


class WorkflowViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """API endpoint for listing, creating, and updating workflows."""

    serializer_class = WorkflowSerializer
    http_method_names = ["get", "post", "head", "patch", "delete"]
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.OrderingFilter,)

    def get_queryset(self):
        queryset = Workflow.objects.filter(tenant=Tenant.current())
        if "parent_lookup_template" in self.kwargs:
            queryset = queryset.filter(template=self.kwargs["parent_lookup_template"])
        return queryset.order_by("internal_sequence")

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


class RequestViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """API endpoint for listing and creating requests"""

    serializer_class = RequestSerializer
    http_method_names = ["get", "post"]
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.OrderingFilter,)
    ordering = ("-id",)

    def get_queryset(self):
        queryset = Request.objects.filter(tenant=Tenant.current())
        if "parent_lookup_parent" in self.kwargs:
            queryset = queryset.filter(parent=self.kwargs["parent_lookup_parent"])
        return queryset

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


class ActionViewSet(viewsets.ModelViewSet):
    """API endpoint for listing and creating actions"""

    serializer_class = ActionSerializer
    http_method_names = ["get", "post"]
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.OrderingFilter,)
    ordering = ("-id",)

    def get_queryset(self):
        queryset = Action.objects.filter(tenant=Tenant.current())
        if "parent_lookup_request" in self.kwargs:
            queryset = queryset.filter(request=self.kwargs["parent_lookup_request"])
        return queryset

    def perform_create(self, serializer):
        serializer.save(
            request=Request(id=self.kwargs["parent_lookup_request"]),
            user=self.request.user,
            tenant=Tenant.current()
        )
