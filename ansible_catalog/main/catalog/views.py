""" Default views for Catalog."""

import logging

import django_rq
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
)

from ansible_catalog.common.auth import keycloak_django
from ansible_catalog.common.auth.keycloak_django.utils import parse_scope
from ansible_catalog.common.serializers import TaskSerializer
from ansible_catalog.common.tag_mixin import TagMixin
from ansible_catalog.common.image_mixin import ImageMixin
from ansible_catalog.common.queryset_mixin import QuerySetMixin

from ansible_catalog.main.models import Tenant
from ansible_catalog.main.auth.models import Group
from ansible_catalog.main.catalog.exceptions import (
    BadParamsException,
)
from ansible_catalog.main.catalog.models import (
    ApprovalRequest,
    CatalogServicePlan,
    Order,
    Portfolio,
    PortfolioItem,
    ProgressMessage,
)
from ansible_catalog.main.catalog.serializers import (
    ApprovalRequestSerializer,
    CatalogServicePlanSerializer,
    CopyPortfolioSerializer,
    CopyPortfolioItemSerializer,
    ModifiedServicePlanInSerializer,
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

from ansible_catalog.main.catalog.services.collect_tag_resources import (
    CollectTagResources,
)
from ansible_catalog.main.catalog.services.copy_portfolio import (
    CopyPortfolio,
)
from ansible_catalog.main.catalog.services.copy_portfolio_item import (
    CopyPortfolioItem,
)
from ansible_catalog.main.catalog.services.create_portfolio_item import (
    CreatePortfolioItem,
)
from ansible_catalog.main.catalog.services.fetch_service_plans import (
    FetchServicePlans,
)
from ansible_catalog.main.catalog.services.refresh_service_plan import (
    RefreshServicePlan,
)
from ansible_catalog.main.catalog.services.submit_approval_request import (
    SubmitApprovalRequest,
)

from ansible_catalog.main.catalog import tasks

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
                description="Return a list of portfolios. An empty list indicates either undefined portfolios in the system or inaccessibility to the caller.",
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
    QuerySetMixin,
    viewsets.ModelViewSet,
):
    """API endpoint for listing and creating portfolios."""

    serializer_class = PortfolioSerializer
    http_method_names = ["get", "post", "head", "patch", "delete"]
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filterset_fields = ("name", "description", "created_at", "updated_at")
    search_fields = ("name", "description")

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
        portfolio = get_object_or_404(Portfolio, pk=pk)
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
        description=(
            "Share a portfolio with specified groups and permissions."
        ),
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

        data = []
        for permission in permissions:
            group = groups_by_path.get(permission.groups[0])
            scopes = [
                parse_scope(portfolio, scope) for scope in permission.scopes
            ]
            data.append(
                {
                    "group": group.id if group else None,
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
    QuerySetMixin,
    viewsets.ModelViewSet,
):
    """API endpoint for listing and creating portfolio items."""

    serializer_class = PortfolioItemSerializer
    http_method_names = ["get", "post", "head", "patch", "delete"]
    permission_classes = (IsAuthenticated,)
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

        portfolio = request.data.get("portfolio")
        get_object_or_404(Portfolio, pk=portfolio)

        svc = CreatePortfolioItem(request.data).process()
        output_serializer = PortfolioItemSerializer(svc.item, many=False)
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
        portfolio_item = get_object_or_404(PortfolioItem, pk=pk)
        options = {
            "portfolio_item_id": portfolio_item.id,
            "portfolio": portfolio_item.portfolio.id,
            "portfolio_item_name": request.data.get(
                "portfolio_item_name", portfolio_item.name
            ),
        }
        svc = CopyPortfolioItem(portfolio_item, options).process()
        serializer = self.get_serializer(svc.new_portfolio_item)

        return Response(serializer.data)


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
class OrderViewSet(NestedViewSetMixin, QuerySetMixin, viewsets.ModelViewSet):
    """API endpoint for listing and creating orders."""

    serializer_class = OrderSerializer
    http_method_names = ["get", "post", "head", "delete"]
    permission_classes = (IsAuthenticated,)
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
        order = get_object_or_404(Order, pk=pk)

        if not order.product:
            raise BadParamsException(
                _("Order {} does not have related order items").format(
                    order.id
                )
            )

        tag_resources = CollectTagResources(order).process().tag_resources
        message = _("Computed tags for order {}: {}").format(
            order.id, tag_resources
        )
        order.update_message(ProgressMessage.Level.INFO, message)

        logger.info("Creating approval request for order id %d", order.id)
        SubmitApprovalRequest(tag_resources, order).process()

        serializer = self.get_serializer(order)
        return Response(serializer.data)

    # TODO:
    @extend_schema(
        description="Cancel the given order",
        request=None,
        responses={204: None},
    )
    @action(methods=["patch"], detail=True)
    def cancel(self, request, pk):
        """Cancels the specified pk order."""
        pass


@extend_schema_view(
    retrieve=extend_schema(
        tags=("orders", "order_items"),
        description="Get a specific order item based on the order item ID",
        parameters=[
            OpenApiParameter(
                "extra",
                required=False,
                enum=["true", "false"],
                description="Include extra data such as portfolio item details",
            ),
        ],
    ),
    list=extend_schema(
        tags=("orders", "order_items"),
        description="Get a list of order items associated with the logged in user.",
        parameters=[
            OrderItemDocSerializer,
            OpenApiParameter(
                "extra",
                required=False,
                enum=["true", "false"],
                description="Include extra data such as portfolio item details",
            ),
        ],
        responses={
            200: OpenApiResponse(
                OrderItemSerializer,
                description="Return a list of order items. An empty list indicates either undefined orders in the system or inaccessibility to the caller.",
            ),
        },
    ),
    create=extend_schema(
        tags=("orders", "order_items"),
        description="Add an order item to an order in pending state",
    ),
    destroy=extend_schema(
        description="Delete an existing order item",
    ),
)
class OrderItemViewSet(
    NestedViewSetMixin, QuerySetMixin, viewsets.ModelViewSet
):
    """API endpoint for listing and creating order items."""

    serializer_class = OrderItemSerializer
    http_method_names = ["get", "post", "head", "delete"]
    permission_classes = (IsAuthenticated,)
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
        description="Get a list of approval requests associated with an order. As the order is being approved one can check the status of the approvals.",
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
        description="Get a list of progress messages associated with an order. As the order is being processed the provider can update the progress messages.",
    ),
)
class ProgressMessageViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """API endpoint for listing progress messages."""

    serializer_class = ProgressMessageSerializer
    http_method_names = ["get"]
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filterset_fields = (
        "received_at",
        "level",
        "created_at",
        "updated_at",
    )

    def get_queryset(self):
        """return queryset based on messageable_type"""

        path_splits = self.request.path.split("/")
        parent_type = path_splits[path_splits.index("progress_messages") - 2]
        messageable_id = self.kwargs.get("messageable_id")
        messageable_type = "Order" if parent_type == "orders" else "OrderItem"

        return ProgressMessage.objects.filter(
            tenant=Tenant.current(),
            messageable_type=messageable_type,
            messageable_id=messageable_id,
        )


@extend_schema_view(
    retrieve=extend_schema(
        description="Get a specific service plan",
    ),
)
class CatalogServicePlanViewSet(
    NestedViewSetMixin, QuerySetMixin, viewsets.ModelViewSet
):
    """API endpoint for listing and creating catalog service plans"""

    pagination_class = None
    queryset = CatalogServicePlan.objects.all()
    serializer_class = CatalogServicePlanSerializer
    http_method_names = ["get", "patch", "post", "head"]
    permission_classes = (IsAuthenticated,)
    filter_backends = []  # no filtering is needed
    parent_field_names = ("portfolio_item",)

    @extend_schema(
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
        responses={200: CatalogServicePlanSerializer},
    )
    def retrieve(self, request, pk):
        service_plan = get_object_or_404(CatalogServicePlan, pk=pk)

        RefreshServicePlan(service_plan).process()

        serializer = CatalogServicePlanSerializer(
            service_plan, many=False, context=self.get_serializer_context()
        )
        return Response(serializer.data)

    @extend_schema(
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
        responses={200: CatalogServicePlanSerializer},
    )
    def list(self, request, *args, **kwargs):
        portfolio_item_id = kwargs.pop("portfolio_item_id")
        portfolio_item = get_object_or_404(PortfolioItem, pk=portfolio_item_id)

        service_plans = (
            FetchServicePlans(portfolio_item).process().service_plans
        )
        serializer = CatalogServicePlanSerializer(
            service_plans, many=True, context=self.get_serializer_context()
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        description="Modify the schema of the service plan",
        request=ModifiedServicePlanInSerializer,
        responses={200: CatalogServicePlanSerializer},
    )
    def partial_update(self, request, pk):
        service_plan = get_object_or_404(CatalogServicePlan, pk=pk)

        serializer = ModifiedServicePlanInSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        modified = request.data["modified"]
        service_plan.modified_schema = modified
        service_plan.save()

        RefreshServicePlan(service_plan).process()

        output_serializer = CatalogServicePlanSerializer(
            service_plan, context=self.get_serializer_context()
        )
        return Response(output_serializer.data)

    @extend_schema(
        description="Reset the schema of the service plan. It deletes any user modifications and pulls in latest schema from inventory",
        request=None,
        responses={200: CatalogServicePlanSerializer},
    )
    @action(methods=["post"], detail=True)
    def reset(self, request, pk):
        """Reset the specified service plan."""
        service_plan = get_object_or_404(CatalogServicePlan, pk=pk)

        service_plan.modified_schema = None
        svc = RefreshServicePlan(service_plan).process()

        serializer = CatalogServicePlanSerializer(
            svc.service_plan, many=False, context=self.get_serializer_context()
        )
        return Response(serializer.data)
