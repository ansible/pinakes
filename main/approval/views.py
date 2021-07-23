""" Default views for Approval."""
import logging

from rest_framework import viewsets, status, filters
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
    ActionSerializer,
)

logger = logging.getLogger("approval")

class TemplateViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """API endpoint for listing and templates."""

    queryset = Template.objects.filter(tenant=Tenant.current())
    http_method_names = ["get", "head"]
    permission_classes = (IsAuthenticated,)
    serializer_class = TemplateSerializer
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = "__all__" # This line is optional, default
    ordering = ("-id",)


class WorkflowViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """API endpoint for listing, creating, and updating workflows."""

    queryset = Workflow.objects.filter(tenant=Tenant.current()).order_by("-internal_sequence")
    serializer_class = WorkflowSerializer
    http_method_names = ["get", "post", "head", "patch", "delete"]
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.OrderingFilter,)


class RequestViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """API endpoint for listing and creating requests"""

    queryset = Request.objects.filter(tenant=Tenant.current())
    serializer_class = RequestSerializer
    http_method_names = ["get", "post"]
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.OrderingFilter,)
    ordering = ("-id",)

    def create(self, request, *args, **kwargs):
        serializer = RequestInSerializer(data=request.data, context={"request": request})
        output_serializer = serializer # default
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST)
        try:
            output_serializer = RequestSerializer(serializer.save())
        except Exception as error:
            raise ValidationError({"detail": error}) from error
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class ActionViewSet(viewsets.ModelViewSet):
    """API endpoint for listing and creating actions"""

    queryset = Action.objects.filter(tenant=Tenant.current())
    serializer_class = ActionSerializer
    http_method_names = ["get", "post"]
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.OrderingFilter,)
    ordering = ("-id",)
