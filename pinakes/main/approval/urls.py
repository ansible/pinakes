"""URLs for approval"""
from pinakes.common.nested_router import (
    NestedDefaultRouter,
)
from pinakes.main.approval.views import (
    NotificationSettingViewSet,
    NotificationTypeViewSet,
    TemplateViewSet,
    WorkflowViewSet,
    RequestViewSet,
    ActionViewSet,
)

urls_views = {}

router = NestedDefaultRouter()
router.register(
    "notifications_settings",
    NotificationSettingViewSet,
    basename="notificationsetting",
)
router.register(
    "notification_types", NotificationTypeViewSet, basename="notificationtype"
)

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
urls_views["template-workflow-list"] = WorkflowViewSet.as_view(
    {"get": "list"}
)  # list only

router.register("workflows", WorkflowViewSet, basename="workflow")

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
urls_views["request-request-content"] = None
urls_views["request-request-list"] = RequestViewSet.as_view(
    {"get": "list"}
)  # list only

router.register("actions", ActionViewSet, basename="action")
urls_views["action-list"] = None
