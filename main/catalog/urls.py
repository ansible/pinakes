from django.urls import include, path
from rest_framework import routers

from rest_framework_extensions.routers import NestedRouterMixin

from main.catalog.views import (
    TenantViewSet,
    PortfolioViewSet,
    PortfolioItemViewSet,
    OrderViewSet,
    OrderItemViewSet,
    ApprovalRequestViewSet,
    ProgressMessageViewSet,
)


class NestedDefaultRouter(NestedRouterMixin, routers.DefaultRouter):
    pass


router = NestedDefaultRouter()

router.register("tenants", TenantViewSet)
portfolios = router.register(r"portfolios", PortfolioViewSet)
portfolios.register(
    r"portfolio_items",
    PortfolioItemViewSet,
    basename="portfolio-portfolioitem",
    parents_query_lookups=["portfolio"],
)
portfolio_items = router.register(r"portfolio_items", PortfolioItemViewSet)

orders = router.register(r"orders", OrderViewSet)
orders.register(
    r"order_items",
    OrderItemViewSet,
    basename="order-orderitem",
    parents_query_lookups=["order"],
)
orders.register(
    r"approval_request",
    ApprovalRequestViewSet,
    basename="order-approvalrequest",
    parents_query_lookups=["order"],
)
orders.register(
    r"progress_messages",
    ProgressMessageViewSet,
    basename="order-progressmessage",
    parents_query_lookups=["messageable_id"],
)

order_items = router.register(r"order_items", OrderItemViewSet)
order_items.register(
    r"progress_messages",
    ProgressMessageViewSet,
    basename="orderitem-progressmessage",
    parents_query_lookups=["messageable_id"],
)

urlpatterns = [
    path("", include((router.urls, "catalog"))),
]
