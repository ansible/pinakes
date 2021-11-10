"""URLs for Inventory"""
from ansible_catalog.common.nested_router import NestedDefaultRouter
from ansible_catalog.main.inventory.views import (
    ServiceInstanceViewSet,
    ServiceInventoryViewSet,
    SourceViewSet,
    ServicePlanViewSet,
    ServiceOfferingViewSet,
)

urls_views = {}

router = NestedDefaultRouter()
sources = router.register(r"sources", SourceViewSet, basename="source")
sources.register(
    r"service_inventories",
    ServiceInventoryViewSet,
    basename="source-service_inventory",
    parents_query_lookups=ServiceInventoryViewSet.parent_field_names,
)
urls_views["source-service_inventory-detail"] = None  # disable
urls_views["source-service_inventory-tag"] = None
urls_views["source-service_inventory-tags"] = None
urls_views["source-service_inventory-untag"] = None

sources.register(
    r"service_plans",
    ServicePlanViewSet,
    basename="source-service_plan",
    parents_query_lookups=(ServicePlanViewSet.parent_field_names[1],),
)
urls_views["source-service_plan-detail"] = None

sources.register(
    r"service_offerings",
    ServiceOfferingViewSet,
    basename="source-service_offering",
    parents_query_lookups=ServiceOfferingViewSet.parent_field_names,
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
    parents_query_lookups=(ServicePlanViewSet.parent_field_names[0],),
)
urls_views["offering-service_plans-detail"] = None

router.register(
    "service_inventories", ServiceInventoryViewSet, basename="serviceinventory"
)
urls_views["serviceinventory-list"] = ServiceInventoryViewSet.as_view(
    {"get": "list"}
)  # list only
router.register("service_plans", ServicePlanViewSet, basename="serviceplan")
router.register(
    "service_instances", ServiceInstanceViewSet, basename="serviceinstance"
)
