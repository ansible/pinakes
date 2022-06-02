"""Default views for Catalog."""

import logging

import django_rq
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_noop
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
)

from pinakes.common.auth import keycloak_django
from pinakes.common.auth.keycloak_django.utils import (
    parse_scope,
)
from pinakes.common.auth.keycloak_django.views import (
    KeycloakPermissionMixin,
)
from pinakes.common.serializers import TaskSerializer
from pinakes.common.tag_mixin import TagMixin
from pinakes.common.image_mixin import ImageMixin
from pinakes.common.queryset_mixin import QuerySetMixin

from pinakes.main.models import Tenant
from pinakes.main.common.models import Group
from pinakes.main.catalog.exceptions import (
    BadParamsException,
)
from pinakes.main.catalog.models import (
    ApprovalRequest,
    ServicePlan,
    Portfolio,
    PortfolioItem,
    ProgressMessage,
    Order,
    OrderItem,
)
from pinakes.main.catalog import permissions
from pinakes.main.catalog.serializers import (
    ApprovalRequestSerializer,
    ServicePlanSerializer,
    CopyPortfolioSerializer,
    CopyPortfolioItemSerializer,
    ModifiedServicePlanInSerializer,
    NextNameInSerializer,
    NextNameOutSerializer,
    OrderItemSerializer,
    OrderItemDocSerializer,
    OrderSerializer,
    PortfolioItemSerializer,
    PortfolioItemInSerializer,
    PortfolioSerializer,
    ProgressMessageSerializer,
    TenantSerializer,
    SharingRequestSerializer,
    SharingPermissionSerializer,
)

from pinakes.main.catalog.services.cancel_order import (
    CancelOrder,
)
from pinakes.main.catalog.services.collect_tag_resources import (
    CollectTagResources,
)
from pinakes.main.catalog.services.copy_portfolio import (
    CopyPortfolio,
)
from pinakes.main.catalog.services.copy_portfolio_item import (
    CopyPortfolioItem,
)
from pinakes.main.catalog.services import (
    name,
)
from pinakes.main.catalog.services.refresh_service_plan import (
    RefreshServicePlan,
)
from pinakes.main.catalog.services.submit_approval_request import (
    SubmitApprovalRequest,
)
from pinakes.main.catalog.services.validate_order_item import (
    ValidateOrderItem,
)

from pinakes.main.catalog import tasks

# Create your views here.

logger = logging.getLogger("catalog")


@extend_schema_view(
    retrieve=extend_schema(
        description="Get a tenant by its id",
    ),
    list=extend_schema(
        description="List all tenants",
    ),
)
class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for listing tenants."""

    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ("id",)
    filterset_fields = "__all__"


@extend_schema_view(
    retrieve=extend_schema(
        description="Get a portfolio by its id",
    ),
    list=extend_schema(
        description="List all portfolios",
        responses={
            200: OpenApiResponse(
                response=PortfolioSerializer,
                description=(
                    "Return a list of portfolios. An empty list indicates"
                    " either undefined portfolios in the system or"
                    " inaccessibility to the caller."
                ),
            )
        },
    ),
    create=extend_schema(
        description="Create a new portfolio",
    ),
    partial_update=extend_schema(
        description="Edit an existing portfolio",
    ),
    destroy=extend_schema(
        description="Delete an existing portfolio",
    ),
)
class PortfolioViewSet(
    ImageMixin,
    TagMixin,
    NestedViewSetMixin,
    KeycloakPermissionMixin,
    QuerySetMixin,
    viewsets.ModelViewSet,
):
    """API endpoint for listing and creating portfolios."""

    serializer_class = PortfolioSerializer
    http_method_names = ["get", "post", "head", "patch", "delete"]
    permission_classes = (IsAuthenticated,)
    keycloak_permission = permissions.PortfolioPermission
    ordering = ("-id",)
    filterset_fields = ("name", "description", "created_at", "updated_at")
    search_fields = (
        "name",
        "description",
        "user__first_name",
        "user__last_name",
        "user__username",
    )

    @extend_schema(
        description="Make a copy of the portfolio",
        request=CopyPortfolioSerializer,
        responses={
            200: OpenApiResponse(
                PortfolioSerializer, description="The new portfolio"
            )
        },
    )
    @action(methods=["post"], detail=True)
    def copy(self, request, pk):
        """Copy the specified pk portfolio."""
        portfolio = self.get_object()
        options = {
            "portfolio": portfolio,
            "portfolio_name": request.data.get(
                "portfolio_name", portfolio.name
            ),
        }

        svc = CopyPortfolio(portfolio, options).process()
        serializer = self.get_serializer(svc.new_portfolio)

        return Response(serializer.data)

    @extend_schema(
        description="Share a portfolio with specified groups and permissions.",
        request=SharingRequestSerializer,
        responses={status.HTTP_202_ACCEPTED: TaskSerializer},
    )
    @action(methods=["post"], detail=True)
    def share(self, request, pk=None):
        portfolio = self.get_object()
        data = self._parse_share_policy(request, portfolio)
        group_ids = [group.id for group in data["groups"]]

        job = django_rq.enqueue(
            tasks.add_portfolio_permissions,
            portfolio.id,
            group_ids,
            data["permissions"],
        )
        serializer = TaskSerializer(job)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        description=(
            "Remove a portfolio sharing with specified groups and permissions."
        ),
        request=SharingRequestSerializer,
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_202_ACCEPTED: TaskSerializer,
        },
    )
    @action(methods=["post"], detail=True)
    def unshare(self, request, pk=None):
        portfolio = self.get_object()
        data = self._parse_share_policy(request, portfolio)

        if portfolio.keycloak_id is None:
            return Response(status=status.HTTP_200_OK)

        group_ids = [group.id for group in data["groups"]]
        job = django_rq.enqueue(
            tasks.remove_portfolio_permissions,
            portfolio.id,
            group_ids,
            data["permissions"],
        )
        serializer = TaskSerializer(job)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        description="Retrieve a portfolio sharing info.",
        responses=SharingPermissionSerializer(many=True),
    )
    @action(
        methods=["get"],
        detail=True,
        pagination_class=None,
        filterset_fields=None,
    )
    def share_info(self, request, pk=None):
        portfolio = self.get_object()
        if not portfolio.keycloak_id:
            return Response([])

        client = keycloak_django.get_uma_client()
        permissions = client.find_permissions_by_resource(
            portfolio.keycloak_id
        )
        permissions = list(
            filter(keycloak_django.is_group_permission, permissions)
        )

        groups_lookup = [permission.groups[0] for permission in permissions]
        groups = Group.objects.filter(path__in=groups_lookup)
        groups_by_path = {group.path: group for group in groups}

        permissions_by_group = {}
        for permission in permissions:
            if permission.groups[0] in permissions_by_group:
                permissions_by_group[permission.groups[0]].extend(
                    permission.scopes
                )
            else:
                permissions_by_group[permission.groups[0]] = permission.scopes

        data = []
        for path, scopes in permissions_by_group.items():
            group = groups_by_path.get(path)
            scopes = [parse_scope(portfolio, scope) for scope in scopes]
            data.append(
                {
                    "group_id": group.id if group else None,
                    "group_name": group.name if group else None,
                    "permissions": scopes,
                }
            )
        return Response(data)

    def _parse_share_policy(self, request, portfolio):
        serializer = SharingRequestSerializer(
            data=request.data,
            context={
                "valid_scopes": portfolio.keycloak_actions(),
            },
        )
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def perform_destroy(self, instance):
        if instance.keycloak_id:
            client = keycloak_django.get_uma_client()
            client.delete_resource(instance.keycloak_id)
        super().perform_destroy(instance)


@extend_schema_view(
    retrieve=extend_schema(
        description="Get a portfolio item by its id",
    ),
    list=extend_schema(
        description="List all portfolio items",
    ),
    partial_update=extend_schema(
        description="Edit an existing portfolio item",
    ),
    destroy=extend_schema(
        description="Delete an existing portfolio item",
    ),
)
class PortfolioItemViewSet(
    ImageMixin,
    TagMixin,
    NestedViewSetMixin,
    KeycloakPermissionMixin,
    QuerySetMixin,
    viewsets.ModelViewSet,
):
    """API endpoint for listing and creating portfolio items."""

    serializer_class = PortfolioItemSerializer
    http_method_names = ["get", "post", "head", "patch", "delete"]
    permission_classes = (IsAuthenticated,)
    keycloak_permission = permissions.PortfolioItemPermission
    ordering = ("-id",)
    filterset_fields = (
        "name",
        "description",
        "service_offering_ref",
        "portfolio",
        "created_at",
        "updated_at",
    )
    search_fields = ("name", "description")
    parent_field_names = ("portfolio",)

    @extend_schema(
        description="Create a new portfolio item",
        request=PortfolioItemInSerializer,
    )
    def create(self, request, *args, **kwargs):
        serializer = PortfolioItemInSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        portfolio_id = request.data.get("portfolio")
        portfolio = get_object_or_404(Portfolio, pk=portfolio_id)
        self.check_object_permissions(request, portfolio)

        output_serializer = PortfolioItemSerializer(
            serializer.save(user=self.request.user),
            context=self.get_serializer_context(),
        )

        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        description="Make a copy of the portfolio item",
        request=CopyPortfolioItemSerializer,
        responses={
            200: OpenApiResponse(
                PortfolioItemSerializer,
                description="The copied portfolio item",
            )
        },
    )
    @action(methods=["post"], detail=True)
    def copy(self, request, pk):
        """Copy the specified pk portfolio item."""
        portfolio_item_src = self.get_object()

        # TODO: Move to serializer
        portfolio_id_dest = request.data.get("portfolio_id", None)
        if portfolio_id_dest:
            portfolio_dest = get_object_or_404(Portfolio, id=portfolio_id_dest)
        else:
            portfolio_dest = portfolio_item_src.portfolio
        self.get_keycloak_permission().perform_check_object_permission(
            "update", request, self, portfolio_dest
        )
        portfolio_item_name = request.data.get(
            "portfolio_item_name", portfolio_item_src.name
        )

        svc = CopyPortfolioItem(
            portfolio_item_src, portfolio_dest, portfolio_item_name
        ).process()
        serializer = self.get_serializer(svc.new_portfolio_item)

        return Response(serializer.data)

    @extend_schema(
        description="Get next available portfolio item name",
        parameters=[
            OpenApiParameter(
                "destination_portfolio_id",
                required=False,
                description=(
                    "Retrieve next available portfolio item name from"
                    " destination portfolio"
                ),
            ),
        ],
        request=NextNameInSerializer,
        responses={
            200: OpenApiResponse(
                NextNameOutSerializer(many=False),
                description="The next available portfolio item name",
            )
        },
    )
    @action(methods=["get"], detail=True)
    def next_name(self, request, pk):
        """Retrieve next available portfolio item name"""
        portfolio_item = get_object_or_404(PortfolioItem, pk=pk)
        destination_portfolio_id = request.GET.get(
            "destination_portfolio_id", None
        )
        portfolio = (
            portfolio_item.portfolio
            if destination_portfolio_id is None
            else Portfolio.objects.get(id=destination_portfolio_id)
        )

        portfolio_item_names = [
            item.name
            for item in PortfolioItem.objects.filter(portfolio=portfolio)
        ]
        available_name = name.create_copy_name(
            portfolio_item.name, portfolio_item_names
        )

        output_serializer = NextNameOutSerializer(
            {"next_name": available_name}
        )
        return Response(output_serializer.data)


@extend_schema_view(
    retrieve=extend_schema(
        description="Get a specific order based on the order ID",
        parameters=[
            OpenApiParameter(
                "extra",
                required=False,
                enum=["true", "false"],
                description="Include extra data such as order items",
            ),
        ],
    ),
    list=extend_schema(
        description="Get a list of orders associated with the logged in user.",
        parameters=[
            OrderSerializer,
            OpenApiParameter(
                "extra",
                required=False,
                enum=["true", "false"],
                description="Include extra data such as order items",
            ),
        ],
    ),
    create=extend_schema(
        description="Create a new order",
    ),
    destroy=extend_schema(
        description="Delete an existing order",
    ),
)
class OrderViewSet(
    NestedViewSetMixin,
    KeycloakPermissionMixin,
    QuerySetMixin,
    viewsets.ModelViewSet,
):
    """API endpoint for listing and creating orders."""

    serializer_class = OrderSerializer
    http_method_names = ["get", "post", "patch", "head", "delete"]
    permission_classes = (IsAuthenticated,)
    keycloak_permission = permissions.OrderPermission
    ordering = ("-id",)
    filterset_fields = (
        "state",
        "order_request_sent_at",
        "created_at",
        "updated_at",
        "completed_at",
    )
    search_fields = ("state",)

    @extend_schema(
        description="Submit the given order",
        request=None,
        responses={200: OrderSerializer},
    )
    @action(methods=["post"], detail=True)
    def submit(self, request, pk):
        """Orders the specified pk order."""
        order = self.get_object()
        if not order.product:
            raise BadParamsException(
                _("Order {} does not have related order items").format(
                    order.id
                )
            )

        ValidateOrderItem(order.product).process()

        tag_resources = CollectTagResources(order).process().tag_resources

        message = gettext_noop(
            "Computed tags for order %(order_id)d: %(tag_resources)s"
        )
        params = {"order_id": order.id, "tag_resources": tag_resources}
        order.update_message(ProgressMessage.Level.INFO, message, params)

        logger.info("Creating approval request for order id %d", order.id)
        if request and request.META:
            http_host = (
                request.META.get("HTTP_HOST")
                or request.META.get("REMOTE_HOST")
                or request.META.get("HTTP_ORIGIN")
            )
            context = {"http_host": http_host}
        else:
            context = {}
        SubmitApprovalRequest(tag_resources, order, context).process()

        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @extend_schema(
        description="Cancel the given order",
        request=None,
        responses={204: None},
    )
    @action(methods=["patch"], detail=True)
    def cancel(self, request, pk):
        """Cancels the specified pk order."""
        order = self.get_object()

        svc = CancelOrder(order).process()
        serializer = self.get_serializer(svc.order)

        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    retrieve=extend_schema(
        tags=["orders", "order_items"],
        description="Get a specific order item based on the order item ID",
        parameters=[
            OpenApiParameter(
                "extra",
                required=False,
                enum=["true", "false"],
                description=(
                    "Include extra data such as portfolio item details"
                ),
            ),
        ],
    ),
    list=extend_schema(
        tags=["orders", "order_items"],
        description=(
            "Get a list of order items associated with the logged in user."
        ),
        parameters=[
            OrderItemDocSerializer,
            OpenApiParameter(
                "extra",
                required=False,
                enum=["true", "false"],
                description=(
                    "Include extra data such as portfolio item details"
                ),
            ),
        ],
        responses={
            200: OpenApiResponse(
                OrderItemSerializer,
                description=(
                    "Return a list of order items. An empty list indicates"
                    " either undefined orders in the system or inaccessibility"
                    " to the caller."
                ),
            ),
        },
    ),
    create=extend_schema(
        tags=["orders", "order_items"],
        description="Add an order item to an order in pending state",
    ),
    destroy=extend_schema(
        description="Delete an existing order item",
    ),
)
class OrderItemViewSet(
    NestedViewSetMixin,
    KeycloakPermissionMixin,
    QuerySetMixin,
    viewsets.ModelViewSet,
):
    """API endpoint for listing and creating order items."""

    serializer_class = OrderItemSerializer
    http_method_names = ["get", "post", "head", "delete"]
    permission_classes = (IsAuthenticated,)
    keycloak_permission = permissions.OrderItemPermission
    ordering = ("-id",)
    filterset_fields = (
        "name",
        "count",
        "state",
        "portfolio_item",
        "order",
        "external_url",
        "order_request_sent_at",
        "created_at",
        "updated_at",
        "completed_at",
    )
    search_fields = ("name", "state")
    parent_field_names = ("order",)

    def perform_create(self, serializer):
        serializer.save(
            order_id=self.kwargs["order_id"],
        )


@extend_schema_view(
    list=extend_schema(
        description=(
            "Get a list of approval requests associated with an order. As the"
            " order is being approved one can check the status of the"
            " approvals."
        ),
    ),
)
class ApprovalRequestViewSet(
    NestedViewSetMixin, QuerySetMixin, viewsets.ModelViewSet
):
    """API endpoint for listing approval requests."""

    queryset = ApprovalRequest.objects.all()
    serializer_class = ApprovalRequestSerializer
    http_method_names = ["get"]
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filterset_fields = (
        "order",
        "approval_request_ref",
        "state",
        "reason",
        "request_completed_at",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "state",
        "reason",
    )
    parent_field_names = ("order",)


@extend_schema_view(
    list=extend_schema(
        description=(
            "Get a list of progress messages associated with an order. As the"
            " order is being processed the provider can update the progress"
            " messages."
        ),
    ),
)
class _BaseProgressMessageViewSet(
    NestedViewSetMixin, KeycloakPermissionMixin, viewsets.ModelViewSet
):
    """API endpoint for listing progress messages."""

    serializer_class = ProgressMessageSerializer
    http_method_names = ["get"]
    permission_classes = (IsAuthenticated,)
    keycloak_permission = permissions.ProgressMessagePermission
    ordering = ("-id",)
    filterset_fields = (
        "received_at",
        "level",
        "created_at",
        "updated_at",
    )
    messageable_model = None

    @property
    def messageable_type(self) -> str:
        return self.messageable_model.__name__

    def get_queryset(self):
        messageable_id = self.kwargs["messageable_id"]
        return ProgressMessage.objects.filter(
            tenant=Tenant.current(),
            messageable_type=self.messageable_type,
            messageable_id=messageable_id,
        )


class OrderProgressMessageViewSet(_BaseProgressMessageViewSet):
    messageable_model = Order


class OrderItemProgressMessageViewSet(_BaseProgressMessageViewSet):
    messageable_model = OrderItem


@extend_schema_view(
    retrieve=extend_schema(
        description="Get the service plan by the specific ID",
        parameters=[
            OpenApiParameter(
                "extra",
                required=False,
                enum=["true", "false"],
                description="Include extra data such as base_schema",
            ),
        ],
        request=None,
        responses={200: ServicePlanSerializer},
    ),
    list=extend_schema(
        description="List all service plans of the portfolio item",
        parameters=[
            OpenApiParameter(
                "extra",
                required=False,
                enum=["true", "false"],
                description="Include extra data such as base_schema",
            ),
        ],
        request=None,
        responses={200: ServicePlanSerializer},
    ),
)
class ServicePlanViewSet(
    NestedViewSetMixin,
    KeycloakPermissionMixin,
    QuerySetMixin,
    viewsets.ModelViewSet,
):
    """API endpoint for listing and creating service plans"""

    pagination_class = None
    queryset = ServicePlan.objects.all()
    serializer_class = ServicePlanSerializer
    http_method_names = ["get", "patch", "post", "head"]
    permission_classes = (IsAuthenticated,)
    keycloak_permission = permissions.ServicePlanPermission
    filter_backends = []  # no filtering is needed
    parent_field_names = ("portfolio_item",)

    @extend_schema(
        description="Modify the schema of the service plan",
        request=ModifiedServicePlanInSerializer,
        responses={200: ServicePlanSerializer},
    )
    def partial_update(self, request, pk):
        service_plan = get_object_or_404(ServicePlan, pk=pk)

        serializer = ModifiedServicePlanInSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service_plan.modified_schema = request.data["modified"]
        service_plan.save()

        output_serializer = ServicePlanSerializer(
            service_plan, context=self.get_serializer_context()
        )
        return Response(output_serializer.data)

    @extend_schema(
        description=(
            "Reset the schema of the service plan. It deletes any user"
            " modifications and pulls in latest schema from inventory"
        ),
        request=None,
        responses={200: ServicePlanSerializer},
    )
    @action(methods=["post"], detail=True)
    def reset(self, request, pk):
        """Reset the specified service plan."""
        service_plan = get_object_or_404(ServicePlan, pk=pk)

        service_plan.modified_schema = None
        service_plan.base_schema = None
        service_plan.base_sha256 = None
        svc = RefreshServicePlan(service_plan).process()

        serializer = ServicePlanSerializer(
            svc.service_plan, many=False, context=self.get_serializer_context()
        )
        return Response(serializer.data)
