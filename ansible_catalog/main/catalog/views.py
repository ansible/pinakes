""" Default views for Catalog."""

import logging
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from ansible_catalog.common.auth import keycloak_django
from ansible_catalog.common.tag_mixin import TagMixin
from ansible_catalog.common.image_mixin import ImageMixin
from ansible_catalog.common.queryset_mixin import QuerySetMixin

from ansible_catalog.main.models import Tenant
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
    CatalogServicePlanInSerializer,
    OrderItemSerializer,
    OrderSerializer,
    PortfolioItemSerializer,
    PortfolioSerializer,
    ProgressMessageSerializer,
    TenantSerializer,
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
from ansible_catalog.main.catalog.services.fetch_service_plans import (
    FetchServicePlans,
)
from ansible_catalog.main.catalog.services.import_service_plan import (
    ImportServicePlan,
)
from ansible_catalog.main.catalog.services.jsonify_service_plan import (
    JsonifyServicePlan,
)
from ansible_catalog.main.catalog.services.reset_service_plan import (
    ResetServicePlan,
)
from ansible_catalog.main.catalog.services.submit_approval_request import (
    SubmitApprovalRequest,
)

# Create your views here.

logger = logging.getLogger("catalog")


class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for listing and creating tenants."""

    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ("id",)
    filterset_fields = "__all__"


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
        responses={200: PortfolioSerializer},
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
        responses={200: PortfolioItemSerializer},
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
        request=None,
        responses={204: None},
    )
    @action(methods=["patch"], detail=True)
    def cancel(self, request, pk):
        """Cancels the specified pk order."""
        pass


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

    def list(self, request, *args, **kwargs):
        order_id = kwargs.pop("order_id")
        approval_request = ApprovalRequest.objects.get(order_id=order_id)

        serializer = self.get_serializer(approval_request)
        return Response(serializer.data)


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


class CatalogServicePlanViewSet(
    NestedViewSetMixin, QuerySetMixin, viewsets.ModelViewSet
):
    """API endpoint for listing and creating catalog service plans"""

    queryset = CatalogServicePlan.objects.all()
    serializer_class = CatalogServicePlanSerializer
    http_method_names = ["get", "patch", "post", "head"]
    permission_classes = (IsAuthenticated,)
    ordering = ("-id",)
    filterset_fields = (
        "name",
        "portfolio_item",
    )
    search_fields = ("name",)
    parent_field_names = ("portfolio_item",)

    @extend_schema(
        request=None,
        responses={200: CatalogServicePlanSerializer},
    )
    def list(self, request, *args, **kwargs):
        portfolio_item_id = kwargs.pop("portfolio_item_id")
        portfolio_item = PortfolioItem.objects.get(id=portfolio_item_id)

        service_plans = (
            FetchServicePlans(portfolio_item).process().service_plans
        )
        page = self.paginate_queryset(service_plans)
        if page is not None:
            serializer = CatalogServicePlanSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        else:
            serializer = CatalogServicePlanSerializer(service_plans, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=CatalogServicePlanInSerializer,
        responses={201: CatalogServicePlanSerializer},
    )
    def create(self, request, *args, **kwargs):
        serializer = CatalogServicePlanInSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        portfolio_item_id = request.data.pop("portfolio_item_id")
        portfolio_item = PortfolioItem.objects.get(id=portfolio_item_id)

        svc = ImportServicePlan(portfolio_item).process()
        output_serializer = CatalogServicePlanSerializer(
            svc.reimported_service_plan, many=False
        )
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=None,
        responses={200: CatalogServicePlanSerializer},
    )
    @action(methods=["get"], detail=True)
    def base(self, request, pk):
        """Retrieve the base schema of specified pk service plan."""
        service_plan = get_object_or_404(CatalogServicePlan, pk=pk)
        options = {"schema": "base", "service_plan_id": service_plan.id}

        svc = JsonifyServicePlan(service_plan, options).process()
        serializer = CatalogServicePlanSerializer(svc.json, many=False)
        return Response(serializer.data)

    @action(methods=["get", "patch"], detail=True)
    def modified(self, request, pk):
        """Retrieve or update the schema of the specified pk service plan."""
        service_plan = get_object_or_404(CatalogServicePlan, pk=pk)

        if self.request.method == "GET":
            options = {
                "schema": "modified",
                "service_plan_id": service_plan.id,
            }

            svc = JsonifyServicePlan(service_plan, options).process()
            if svc.json.create_json_schema is not None:
                serializer = CatalogServicePlanSerializer(svc.json, many=False)
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            modified = request.data["modified"]
            service_plan.modified_schema = modified
            service_plan.save()

            # Keep the same response with cloud version
            return Response(service_plan.modified_schema)

    @action(methods=["post"], detail=True)
    def reset(self, request, pk):
        """Reset the specified pk service plan."""
        service_plan = get_object_or_404(CatalogServicePlan, pk=pk)

        svc = ResetServicePlan(service_plan).process()

        if svc.status == ResetServicePlan.OK_STATUS:
            serializer = CatalogServicePlanSerializer(
                svc.reimported_service_plan, many=False
            )
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)


class GroupViewSet(viewsets.ViewSet):
    def list(self, request):
        client = keycloak_django.get_admin_client()
        groups = client.list_groups()
        return Response([g.dict(exclude_unset=True) for g in groups])
