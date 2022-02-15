from rest_framework.routers import SimpleRouter

from automation_services_catalog.main.common import views


router = SimpleRouter()
router.register("groups/sync", views.GroupSyncViewSet, basename="group-sync")
router.register("groups", views.GroupViewSet, basename="group")
router.register("tasks", views.TaskViewSet, basename="task")

urlpatterns = router.urls
