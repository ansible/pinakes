"""Default views for Approval."""
import logging
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
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
)

from pinakes.main.models import Tenant
from pinakes.main.approval.models import (
    NotificationType,
    NotificationSetting,
    Workflow,
    Request,
)
from pinakes.main.approval.serializers import (
    NotificationSettingSerializer,
    NotificationTypeSerializer,
    TemplateSerializer,
    WorkflowSerializer,
    RepositionSerializer,
    RequestSerializer,
    ActionSerializer,
    ResourceObjectSerializer,
)
from pinakes.main.approval.services.link_workflow import (
    LinkWorkflow,
)
from pinakes.main.approval.exceptions import (
    InsufficientParamsException,
)
from pinakes.main.approval import validations, permissions
from pinakes.common.queryset_mixin import QuerySetMixin
from pinakes.common.auth.keycloak_django.views import (
    KeycloakPermissionMixin,
)

logger = logging.getLogger("approval")


@extend_schema_view(
    retrieve=extend_schema(
        description="Get a notification type, available to admin only",
    ),
    list=extend_schema(
        description="List all notification types, available to admin only",
    ),
)
class NotificationTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for listing notification types."""

    serializer_class = NotificationTypeSerializer
    queryset = NotificationType.objects.all()
    permission_classes = (
        IsAuthenticated,
        permissions.TemplatePermission,
    )
    serializer_class = NotificationTypeSerializer
    ordering_fields = ("n_type",)
    ordering = ("n_type",)
    search_fields = ("n_type",)


@extend_schema_view(
    retrieve=extend_schema(
        description="Get a notification setting, available to admin only",
    ),
    list=extend_schema(
        description="List all notification settings, available to admin only",
    ),
    create=extend_schema(
        description="Create a notification setting, available to admin only",
    ),
    partial_update=extend_schema(
        description=(
            "Find a notification setting by its id and update its attributes, "
            "available to admin only"
        ),
    ),
    destroy=extend_schema(
        description="Delete a notification setting by its id, available to "
        "admin only",
    ),
)
class NotificationSettingViewSet(viewsets.ModelViewSet):
    """API endpoints for notification settings"""

    http_method_names = ["get", "post", "patch", "delete"]
    serializer_class = NotificationSettingSerializer
    queryset = NotificationSetting.objects.all()
    permission_classes = (
        IsAuthenticated,
        permissions.TemplatePermission,
    )
    serializer_class = NotificationSettingSerializer
    ordering_fields = ("name",)
    ordering = ("name",)
    search_fields = ("name",)

    def perform_create(self, serializer):
        serializer.save(tenant=Tenant.current())


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
        description=(
            "Find a template by its id and update its attributes, available to"
            " admin only"
        ),
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
    permission_classes = (
        IsAuthenticated,
        permissions.TemplatePermission,
    )
    serializer_class = TemplateSerializer
    ordering_fields = ("title", "description")
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
        if num_of_nones == 0:
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
        description=(
            "Get an approval workflow by its id, available to admin only"
        )
    ),
    list=extend_schema(
        description="List workflows, available to admin only",
        parameters=[
            OpenApiParameter(
                "object_type",
                type=str,
                description=(
                    "Object type. Used jointly with object_id and app_name to"
                    " find workflows linked to a resource object"
                ),
            ),
            OpenApiParameter(
                "object_id",
                type=int,
                description=(
                    "ID of the object. Used jointly with object_type and"
                    " app_name to find workflows linked to a resource object"
                ),
            ),
            OpenApiParameter(
                "app_name",
                type=str,
                description=(
                    "Name of the application the object belongs to. Used"
                    " jointly with object_type and object_id to find workflows"
                    " linked to a resource object"
                ),
            ),
        ],
    ),
    create=extend_schema(
        description="Create a workflow, available to admin only",
    ),
    partial_update=extend_schema(
        description=(
            "Find an approval workflow by its id and update its attributes,"
            " available to admin only"
        ),
    ),
    destroy=extend_schema(
        description=(
            "Delete an approval workflow by its id, available to admin only"
        ),
    ),
)
class WorkflowViewSet(
    NestedViewSetMixin, QuerySetMixin, viewsets.ModelViewSet
):
    """API endpoint for listing, creating, and updating workflows."""

    serializer_class = WorkflowSerializer
    http_method_names = ["get", "post", "head", "patch", "delete"]
    permission_classes = (
        IsAuthenticated,
        permissions.WorkflowPermission,
    )
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

    @extend_schema(
        request=RepositionSerializer,
        responses={204: None},
    )
    @action(methods=["post"], detail=True)
    def reposition(self, request, pk):
        """
        Adjust the position of a workflow related to others by an offset number
        """
        serializer = RepositionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "placement" in serializer.validated_data:
            offset = Workflow.objects.count()
            if serializer.validated_data["placement"] == "top":
                offset = -offset
        else:
            offset = serializer.validated_data["increment"]

        workflow = get_object_or_404(Workflow, pk=pk)
        workflow.move_internal_sequence(offset)
        workflow.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        serializer.save(tenant=Tenant.current())


@extend_schema_view(
    retrieve=extend_schema(
        description=(
            "Get an approval request by its id, available to anyone who can"
            " access the request"
        ),
        parameters=[
            OpenApiParameter(
                "extra",
                required=False,
                enum=["true", "false"],
                description=(
                    "Include extra data such as subrequests and actions"
                ),
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
                description=(
                    "Include extra data such as subrequests and actions"
                ),
            ),
            OpenApiParameter(
                "persona",
                required=False,
                enum=["admin", "approver", "requester"],
                description=(
                    "List requests for the user desired persona, default"
                    " requester"
                ),
            ),
        ],
    ),
)
class RequestViewSet(
    NestedViewSetMixin,
    KeycloakPermissionMixin,
    QuerySetMixin,
    viewsets.ModelViewSet,
):
    """API endpoint for listing and creating requests"""

    serializer_class = RequestSerializer
    http_method_names = ["get"]
    ordering = ("-id",)
    filterset_fields = ("name", "description", "state", "decision", "reason")
    search_fields = ("name", "description", "state", "decision", "reason")
    parent_field_names = ("parent",)

    permission_classes = (IsAuthenticated,)
    keycloak_permission = permissions.RequestPermission

    @extend_schema(
        description="Get the content of a request",
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(methods=["get"], detail=True)
    def content(self, request, pk):
        """Retrieve the content of a request"""

        request = get_object_or_404(Request, pk=pk)
        return Response(request.request_context.content)


@extend_schema_view(
    retrieve=extend_schema(
        description="Get an action by its id, available to everyone"
    ),
    list=extend_schema(
        tags=[
            "actions",
            "requests",
        ],
        description=(
            "List actions of a request identified by its id, available to"
            " everyone"
        ),
    ),
    create=extend_schema(
        tags=[
            "actions",
            "requests",
        ],
        description=(
            "Create an action under a request identified by its id. "
            "Admin can create approve, deny, memo, and cancel operations; "
            "approver can create approve, deny, and memo operations; "
            "while requester can create only cancel operation."
        ),
    ),
)
class ActionViewSet(
    KeycloakPermissionMixin, QuerySetMixin, viewsets.ModelViewSet
):
    """API endpoints for listing and creating actions"""

    serializer_class = ActionSerializer
    http_method_names = ["get", "post"]
    permission_classes = (IsAuthenticated,)
    keycloak_permission = permissions.ActionPermission
    ordering = ("-id",)
    filterset_fields = ("operation", "comments")
    search_fields = ("operation", "comments")
    parent_field_names = ("request",)

    def perform_create(self, serializer):
        serializer.save(
            request=self.kwargs["request_id"],
            user=self.request.user,
            tenant=Tenant.current(),
        )
