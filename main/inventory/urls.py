"""URLs for Inventory"""
from rest_framework import routers

from rest_framework_extensions.routers import NestedRouterMixin
from main.inventory.views import (
    ServiceInventoryViewSet,
    SourceViewSet,
    ServicePlanViewSet,
    ServiceOfferingViewSet,
)

urls_views = {}


class NestedDefaultRouter(NestedRouterMixin, routers.DefaultRouter):
    pass


router = NestedDefaultRouter()
sources = router.register(r"sources", SourceViewSet, basename="source")
sources.register(
    r"service_inventories",
    ServiceInventoryViewSet,
    basename="source-service_inventory",
    parents_query_lookups=["source"],
)
urls_views["source-service_inventory-detail"] = None  # disable
urls_views["source-service_inventory-tag"] = None
urls_views["source-service_inventory-tags"] = None
urls_views["source-service_inventory-untag"] = None

sources.register(
    r"service_plans",
    ServicePlanViewSet,
    basename="source-service_plan",
    parents_query_lookups=["source"],
)
urls_views["source-service_plan-detail"] = None

sources.register(
    r"service_offerings",
    ServiceOfferingViewSet,
    basename="source-service_offering",
    parents_query_lookups=["source"],
)
urls_views["source-service_offering-detail"] = None
urls_views["source-service_offering-order"] = None
urls_views["source-service_offering-applied-inventories-tags"] = None

offerings = router.register(
    "service_offerings", ServiceOfferingViewSet, basename="serviceoffering"
)
offerings.register(
    r"service_plans",
    ServicePlanViewSet,
    basename="offering-service_plans",
    parents_query_lookups=["service_offering"],
)
urls_views["offering-service_plans-detail"] = None

router.register(
    "service_inventories", ServiceInventoryViewSet, basename="serviceinventory"
)
router.register("service_plans", ServicePlanViewSet, basename="serviceplan")
