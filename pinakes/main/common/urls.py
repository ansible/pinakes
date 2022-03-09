from rest_framework.routers import SimpleRouter
from django.urls import path

from pinakes.main.common import views


router = SimpleRouter()
router.register("groups/sync", views.GroupSyncViewSet, basename="group-sync")
router.register("groups", views.GroupViewSet, basename="group")
router.register("tasks", views.TaskViewSet, basename="task")


urlpatterns = router.urls + [
    path("about", views.AboutView.as_view(), name="about")
]
