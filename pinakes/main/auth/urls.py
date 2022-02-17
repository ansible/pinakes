from django.urls import path
from django.views.generic import RedirectView

from pinakes.main.auth import views


SOCIAL_AUTH_BACKEND = "keycloak-oidc"

urlpatterns = [
    path(
        "me/", views.CurrentUserViewSet.as_view({"get": "retrieve"}), name="me"
    ),
    path(
        "login/",
        RedirectView.as_view(
            pattern_name="social:begin",
        ),
        name="login",
        kwargs={"backend": SOCIAL_AUTH_BACKEND},
    ),
    path("logout/", views.SessionLogoutView.as_view(), name="logout"),
]
