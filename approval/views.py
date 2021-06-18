""" Default views for Approval."""
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from .basemodel import Tenant
from .models import Template
from .models import Workflow
from .serializers import TenantSerializer
from .serializers import TemplateSerializer
from .serializers import WorkflowSerializer


class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for listing and creating tenants."""

    queryset = Tenant.objects.all().order_by("id")
    serializer_class = TenantSerializer


class TemplateViewSet(viewsets.ModelViewSet):
    """API endpoint for listing and creating templates."""

    queryset = Template.objects.all().order_by("created_at")
    http_method_names = ["get", "post", "head", "patch", "delete"]

    def get_serializer_class(self):
        if self.action == "workflows":
            return WorkflowSerializer
        return TemplateSerializer

    @action(detail=True, url_name="workflows")
    def workflows(self, request, pk=None):
        """sub url template/<id>/workflows"""

        template = self.get_object()
        if request.method == "GET":
            workflows = Workflow.objects.filter(template=template).order_by(
                "created_at"
            )
            page = self.paginate_queryset(workflows)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(workflows, many=True)
            return Response(serializer.data)
        return None


class WorkflowViewSet(viewsets.ModelViewSet):
    """API endpoint for listing and creating workflows."""

    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer
    http_method_names = ["get", "post", "head", "patch", "delete"]
