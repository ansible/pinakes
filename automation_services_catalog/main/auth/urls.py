from django.urls import path

from automation_services_catalog.main.auth import views


urlpatterns = [
    path(
        "me/", views.CurrentUserViewSet.as_view({"get": "retrieve"}), name="me"
    ),
    path("logout/", views.SessionLogoutView.as_view(), name="logout"),
]
