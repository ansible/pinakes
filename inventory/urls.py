"""URLs for Inventory"""
from django.urls import include, path
from rest_framework import routers

from rest_framework_extensions.routers import NestedRouterMixin
from inventory.views import (
    ServiceInventoryViewSet,
    SourceViewSet,
    ServicePlanViewSet,
    ServiceOfferingViewSet,
    ServiceOfferingNodeViewSet
)

class NestedDefaultRouter(NestedRouterMixin, routers.DefaultRouter):
    pass

router = NestedDefaultRouter()
sources = router.register(r'sources', SourceViewSet)
sources.register(
    r'service_inventories',
    ServiceInventoryViewSet,
    basename='source-service_inventory',
    parents_query_lookups=['source']
)

sources.register(
    r'service_plans',
    ServicePlanViewSet,
    basename='source-service_plan',
    parents_query_lookups=['source']
)

sources.register(
    r'service_offerings',
    ServiceOfferingViewSet,
    basename='source-service_offering',
    parents_query_lookups=['source']
)

sources.register(
    r'service_offering_nodes',
    ServiceOfferingNodeViewSet,
    basename='source-service_offering_node',
    parents_query_lookups=['source']
)

offerings = router.register('service_offerings', ServiceOfferingViewSet)
offerings.register(
    r'service_offering_nodes',
    ServiceOfferingNodeViewSet,
    basename='offering-nodes',
    parents_query_lookups=['service_offering']
)
offerings.register(
    r'service_plans',
    ServicePlanViewSet,
    basename='offering-service_plans',
    parents_query_lookups=['service_offering']
)

router.register('service_inventories', ServiceInventoryViewSet)
router.register('service_offering_nodes', ServiceOfferingNodeViewSet)
router.register('service_plans', ServicePlanViewSet)

urlpatterns = [
    path("", include((router.urls, "inventory"))),
]
