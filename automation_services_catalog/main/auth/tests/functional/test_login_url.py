from django.test import Client as TestClient
from django.urls import reverse

from rest_framework import status


def test_login_redirect():
    client = TestClient()
    response = client.get(reverse("auth:login"))

    assert response.status_code == status.HTTP_302_FOUND
    assert response.headers["Location"] == reverse(
        "social:begin", args=("keycloak-oidc",)
    )
