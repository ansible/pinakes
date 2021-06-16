from rest_framework.routers import DefaultRouter
from django.urls import include, path

from .views import TenantViewSet
from .views import TemplateViewSet
from .views import WorkflowViewSet

router = DefaultRouter()
router.register("tenants", TenantViewSet)
router.register("templates", TemplateViewSet)
router.register("workflows", WorkflowViewSet)

urlpatterns = [
    path("", include((router.urls, "approval"))),
]
