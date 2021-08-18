"""URLs for approval"""
from rest_framework.routers import DefaultRouter
from rest_framework_extensions.routers import NestedRouterMixin

from main.approval.views import (
    TemplateViewSet,
    WorkflowViewSet,
    RequestViewSet,
    ActionViewSet,
)

urls_views = {}


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
urls_views["template-workflow-detail"] = None  # disable

router.register("workflows", WorkflowViewSet, basename="workflow")
urls_views["workflow-list"] = WorkflowViewSet.as_view(
    {"get": "list"}
)  # list only

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
urls_views["request-action-detail"] = None  # disable
urls_views["request-request-detail"] = None
urls_views["request-request-full"] = None
urls_views["request-request-list"] = RequestViewSet.as_view(
    {"get": "list"}
)  # list only

router.register("actions", ActionViewSet, basename="action")
urls_views["action-list"] = None
