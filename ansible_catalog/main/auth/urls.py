from rest_framework.routers import SimpleRouter

from ansible_catalog.main.auth import views

router = SimpleRouter()
router.register("groups/sync", views.GroupSyncViewSet, basename="group-sync")
router.register("groups", views.GroupViewSet)

urlpatterns = router.urls
