from django.urls import include, path
from rest_framework import routers

from rest_framework_extensions.routers import NestedRouterMixin

from main.catalog.views import (
    TenantViewSet,
    PortfolioViewSet,
    PortfolioItemViewSet,
    OrderViewSet,
    OrderItemViewSet
)


class NestedDefaultRouter(NestedRouterMixin, routers.DefaultRouter):
    pass


router = NestedDefaultRouter()
router.register("tenants", TenantViewSet)
portfolios = router.register(r'portfolios', PortfolioViewSet)
portfolios.register(
    r"portfolio_items",
    PortfolioItemViewSet,
    basename='portfolio-portfolioitem',
    parents_query_lookups=['portfolio']
)
portfolio_items = router.register(r'portfolio_items', PortfolioItemViewSet)

orders = router.register(r'orders', OrderViewSet)
orders.register(
    r"order_items",
    OrderItemViewSet,
    basename='order-orderitem',
    parents_query_lookups=['order']
)
order_items = router.register(r'order_items', OrderItemViewSet)

urlpatterns = [
    path("", include((router.urls, "catalog"))),
]
