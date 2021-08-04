"""URLs for approval"""
from rest_framework.routers import DefaultRouter
from rest_framework_extensions.routers import NestedRouterMixin
from django.urls import include, path

from main.approval.views import (
    TemplateViewSet,
    WorkflowViewSet,
    RequestViewSet,
    ActionViewSet,
)


class NestedDefaultRouter(NestedRouterMixin, DefaultRouter):
    pass


router = NestedDefaultRouter()

templates = router.register("templates", TemplateViewSet, basename="template")
templates.register(
    "workflows",
    WorkflowViewSet,
    basename="template-workflow",
    parents_query_lookups=["template"],
)

router.register("workflows", WorkflowViewSet, basename="workflow")

requests = router.register("requests", RequestViewSet, basename="request")
requests.register(
    "actions",
    ActionViewSet,
    basename="request-action",
    parents_query_lookups=["request"],
)
requests.register(
    "requests",
    RequestViewSet,
    basename="request-request",
    parents_query_lookups=["parent"],
)

router.register("actions", ActionViewSet, basename="action")

urlpatterns = [
    path("", include((router.urls, "approval"))),
]
