"""URLs for approval"""
from ansible_catalog.common.nested_router import NestedDefaultRouter
from ansible_catalog.main.approval.views import (
    TemplateViewSet,
    WorkflowViewSet,
    RequestViewSet,
    ActionViewSet,
)

urls_views = {}

router = NestedDefaultRouter()
templates = router.register("templates", TemplateViewSet, basename="template")
templates.register(
    "workflows",
    WorkflowViewSet,
    basename="template-workflow",
    parents_query_lookups=WorkflowViewSet.parent_field_names,
)
urls_views["template-workflow-detail"] = None  # disable
urls_views["template-workflow-link"] = None
urls_views["template-workflow-unlink"] = None

router.register("workflows", WorkflowViewSet, basename="workflow")
urls_views["workflow-list"] = WorkflowViewSet.as_view(
    {"get": "list"}
)  # list only

requests = router.register("requests", RequestViewSet, basename="request")
requests.register(
    "actions",
    ActionViewSet,
    basename="request-action",
    parents_query_lookups=ActionViewSet.parent_field_names,
)
requests.register(
    "requests",
    RequestViewSet,
    basename="request-request",
    parents_query_lookups=RequestViewSet.parent_field_names,
)
urls_views["request-action-detail"] = None  # disable
urls_views["request-request-detail"] = None
urls_views["request-request-full"] = None
urls_views["request-request-list"] = RequestViewSet.as_view(
    {"get": "list"}
)  # list only

router.register("actions", ActionViewSet, basename="action")
urls_views["action-list"] = None
