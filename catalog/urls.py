from rest_framework.routers import DefaultRouter

from .views import TenantViewSet
from .views import PortfolioViewSet
from .views import PortfolioItemViewSet

router = DefaultRouter()
router.register("tenants", TenantViewSet)
router.register("portfolios", PortfolioViewSet)
router.register("portfolio_items", PortfolioItemViewSet)
