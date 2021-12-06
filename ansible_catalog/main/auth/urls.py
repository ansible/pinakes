from django.urls import path
from rest_framework.routers import SimpleRouter

from ansible_catalog.main.auth import views

router = SimpleRouter()
router.register("groups/sync", views.GroupSyncViewSet, basename="group-sync")
router.register("groups", views.GroupViewSet)

urlpatterns = [
    path("me/", views.MeView.as_view(), name="me"),
]

urlpatterns += router.urls
