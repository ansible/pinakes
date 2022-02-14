""" Default views for Approval."""
import logging

from decimal import Decimal
from rest_framework.decorators import action
from rest_framework import viewsets, status
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
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
)
from django.utils.translation import gettext_lazy as _

from automation_services_catalog.main.models import Tenant
from automation_services_catalog.main.approval.models import (
    Template,
    Workflow,
    Request,
)
from automation_services_catalog.main.approval.serializers import (
    TemplateSerializer,
    WorkflowSerializer,
    RequestSerializer,
    RequestInSerializer,
    ActionSerializer,
    ResourceObjectSerializer,
)
from automation_services_catalog.main.approval.services.link_workflow import (
    LinkWorkflow,
)
from automation_services_catalog.main.approval.exceptions import (
    InsufficientParamsException,
)
from automation_services_catalog.main.approval import validations
from automation_services_catalog.common.queryset_mixin import QuerySetMixin

logger = logging.getLogger("approval")


@extend_schema_view(
    retrieve=extend_schema(
        description="Get a template by its id, available to admin only",
    ),
    list=extend_schema(
        description="List all templates, available to admin only",
    ),
    create=extend_schema(
        description="Create a template, available to admin only",
    ),
    partial_update=extend_schema(
        description="Find a template by its id and update its attributes, available to admin only",
    ),
    destroy=extend_schema(
        description="Delete a template by its id, available to admin only",
    ),
)
class TemplateViewSet(
    NestedViewSetMixin, QuerySetMixin, viewsets.ModelViewSet
):
    """API endpoint for listing and templates."""

    http_method_names = ["get", "post", "patch", "delete"]
    permission_classes = (IsAuthenticated,)
    serializer_class = TemplateSerializer
    ordering_fields = "__all__"  # This line is optional, default
    ordering = ("-id",)
    search_fields = ("title", "description")

    def perform_create(self, serializer):
        serializer.save(tenant=Tenant.current())


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
            _("Insufficient resource object params: {}").format(
                resource_params
            )
        )


@extend_schema_view(
    retrieve=extend_schema(
        description="Get an approval workflow by its id, available to admin only"
    ),
    list=extend_schema(
        description="List workflows, available to admin only",
    ),
    create=extend_schema(
        tags=(
            "workflows",
            "templates",
        ),
        description="Create a workflow from a template identified by its id, available to admin only",
    ),
    partial_update=extend_schema(
        description="Find an approval workflow by its id and update its attributes, available to admin only",
    ),
    destroy=extend_schema(
        description="Delete an approval workflow by its id, available to admin only",
    ),
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
    parent_field_names = ("template",)
    queryset_order_by = "internal_sequence"

    def retrieve(self, request, *args, **kwargs):
        workflow = self.get_object()
        validations.validate_and_update_approver_groups(workflow, False)
        serializer = self.get_serializer(workflow)
        return Response(serializer.data)

    @extend_schema(
        request=ResourceObjectSerializer,
        responses={204: None},
    )
    @action(methods=["post"], detail=True)
    def link(self, request, pk):
        """
        Link a resource object to a workflow identified by its id,
        available to admin only.
        """

        workflow = get_object_or_404(Workflow, pk=pk)
        validations.validate_and_update_approver_groups(workflow)

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
        """
        Break the link between a resource object selected by the body
        and a workflow by its id, available to admin only
        """

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
            template=Template(id=self.kwargs["template_id"]),
            internal_sequence=next_seq,
            tenant=Tenant.current(),
        )


@extend_schema_view(
    retrieve=extend_schema(
        description="Get an approval request by its id, available to anyone who can access the request",
        parameters=[
            OpenApiParameter(
                "extra",
                required=False,
                enum=["true", "false"],
                description="Include extra data such as subrequests and actions",
            ),
        ],
    ),
    list=extend_schema(
        description="List requests, available to everyone",
        parameters=[
            OpenApiParameter(
                "extra",
                required=False,
                enum=["true", "false"],
                description="Include extra data such as subrequests and actions",
            ),
        ],
    ),
)
class RequestViewSet(NestedViewSetMixin, QuerySetMixin, viewsets.ModelViewSet):
    """API endpoint for listing and creating requests"""

    serializer_class = RequestSerializer
    http_method_names = ["get", "post"]
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filterset_fields = "__all__"
    search_fields = ("name", "description", "state", "decision", "reason")
    parent_field_names = ("parent",)

    @extend_schema(
        description="Create an approval request using given parameters, available to everyone",
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

        output_serializer = RequestSerializer(
            serializer.save(tenant=Tenant.current(), user=self.request.user),
            context=self.get_serializer_context(),
        )
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    retrieve=extend_schema(
        description="Get an action by its id, available to everyone"
    ),
    list=extend_schema(
        tags=(
            "actions",
            "requests",
        ),
        description="List actions of a request identified by its id, available to everyone",
    ),
    create=extend_schema(
        tags=(
            "actions",
            "requests",
        ),
        description="Create an action under a request identified by its id. "
        "Admin can create approve, deny, memo, and cancel operations; "
        "approver can create approve, deny, and memo operations; "
        "while requester can create only cancel operation.",
    ),
)
class ActionViewSet(QuerySetMixin, viewsets.ModelViewSet):
    """API endpoints for listing and creating actions"""

    serializer_class = ActionSerializer
    http_method_names = ["get", "post"]
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filterset_fields = "__all__"
    search_fields = ("operation", "comments")
    parent_field_names = ("request",)

    def perform_create(self, serializer):
        serializer.save(
            request=self.kwargs["request_id"],
            user=self.request.user,
            tenant=Tenant.current(),
        )
