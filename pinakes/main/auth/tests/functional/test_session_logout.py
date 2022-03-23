""" Module to test session logout end point """
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from rest_framework import status
from rest_framework.test import APIClient

from pinakes.common.auth.keycloak_django.authentication import (
    KeycloakSessionAuthentication,
)
from pinakes.common.auth.keycloak_oidc import KeycloakOpenIdConnect


User: AbstractUser = get_user_model()

ACCESS_TOKEN = "DUMMY.ACCESS.TOKEN"
REFRESH_TOKEN = "DUMMY.REFRESH.TOKEN"


@pytest.mark.django_db
def test_session_logout(mocker, admin):
    """Logout an authenticated user from a single session"""
    oidc_client = mocker.patch(
        "pinakes.main.auth.views.get_oidc_client"
    ).return_value

    user = User.objects.create_user(username="test123", password="secret123")
    user.social_auth.create(
        provider=KeycloakSessionAuthentication.social_auth_provider,
        extra_data={
            "access_token": ACCESS_TOKEN,
            "refresh_token": REFRESH_TOKEN,
        },
    )

    client = APIClient()
    client.login(username="test123", password="secret123")

    response = client.post("/api/pinakes/auth/logout/")

    assert response.status_code == status.HTTP_200_OK
    oidc_client.logout_user_session.assert_called_once_with(
        ACCESS_TOKEN,
        REFRESH_TOKEN,
    )


@pytest.mark.django_db
def test_session_logout_bearer_auth(mocker, admin):
    """Logout when using bearer authentication must fail"""
    mocker.patch.object(
        KeycloakOpenIdConnect,
        "user_data",
        return_value={
            "username": "test123",
            "email": "test123@example.com",
            "fullname": "Test User",
            "first_name": "Test",
            "last_name": "User",
        },
    )

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + ACCESS_TOKEN)

    response = client.post("/api/pinakes/auth/logout/")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
