from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from jose import jwt
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.views import APIView

from pinakes.common.auth.keycloak_django.authentication import (
    KeycloakSessionAuthentication,
    KeycloakBearerOfflineAuthentication,
    KeycloakBearerOnlineAuthentication,
)
from pinakes.common.auth.keycloak_oidc import KeycloakOpenIdConnect

User: AbstractUser = get_user_model()

USER_UID = "e993c33a-640f-45e4-8aff-21eed3b2781c"
TOKEN_KEY = "secret"
TOKEN_ISSUER = "https://keycloak.example.com/auth/realms/test"
REFRESH_TOKEN = "DUMMY.REFRESH.TOKEN"
ACCESS_TOKEN = jwt.encode(
    {
        "sub": USER_UID,
        "name": "Fred Sample",
        "preferred_username": "fred",
        "aud": ["account", "pinakes"],
        "iss": TOKEN_ISSUER,
    },
    key=TOKEN_KEY,
)


# NOTE(cutwater): Because some of rest framework settings
#  (i.e. AUTHENTICATION_BACKENDS) are evaluated at module load time,
#  it is not possible to use Django's `@override_settings` decorator.
#  APIView class is patched directly instead.


@pytest.fixture
def testuser():
    user = User.objects.create_user(username="fred")
    user.social_auth.create(
        provider=KeycloakOpenIdConnect.name,
        uid=USER_UID,
        extra_data={
            "access_token": ACCESS_TOKEN,
            "refresh_token": REFRESH_TOKEN,
        },
    )
    user.backend = KeycloakOpenIdConnect
    return user


@pytest.mark.django_db
def test_session_auth(mocker, testuser):
    mocker.patch.object(
        APIView, "authentication_classes", [KeycloakSessionAuthentication]
    )
    authenticate = mocker.spy(KeycloakSessionAuthentication, "authenticate")

    client = APIClient()
    client.force_login(testuser)

    response = client.get("/api/pinakes/auth/me/")

    assert response.status_code == status.HTTP_200_OK

    assert authenticate.call_count == 1
    assert authenticate.spy_return == (testuser, ACCESS_TOKEN)


@pytest.mark.django_db
def test_bearer_offline_auth_new_user(mocker):
    authenticate = mocker.spy(
        KeycloakBearerOfflineAuthentication, "authenticate"
    )
    mocker.patch.object(
        APIView,
        "authentication_classes",
        [KeycloakBearerOfflineAuthentication],
    )
    mocker.patch.multiple(
        KeycloakOpenIdConnect,
        find_valid_key=mock.Mock(return_value=TOKEN_KEY),
        oidc_config=mock.Mock(
            return_value={
                "issuer": TOKEN_ISSUER,
            }
        ),
        JWT_ALGORITHMS=["HS256"],
    )

    user_exists = User.objects.filter(username="fred").exists()
    assert not user_exists

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + ACCESS_TOKEN)

    response = client.get("/api/pinakes/auth/me/")

    assert response.status_code == status.HTTP_200_OK

    try:
        user = User.objects.get(username="fred")
    except User.DoesNotExist:
        pytest.fail("User wasn't created.")

    social_user = user.social_auth.get(provider="keycloak-oidc")
    assert social_user.extra_data == {}

    assert authenticate.call_count == 1
    assert authenticate.spy_return == (user, ACCESS_TOKEN)


@pytest.mark.django_db
def test_bearer_offline_auth_existing_user(mocker, testuser):
    authenticate = mocker.spy(
        KeycloakBearerOfflineAuthentication, "authenticate"
    )
    mocker.patch.object(
        APIView,
        "authentication_classes",
        [KeycloakBearerOfflineAuthentication],
    )
    mocker.patch.multiple(
        KeycloakOpenIdConnect,
        find_valid_key=mock.Mock(return_value=TOKEN_KEY),
        oidc_config=mock.Mock(
            return_value={
                "issuer": TOKEN_ISSUER,
            }
        ),
        JWT_ALGORITHMS=["HS256"],
    )

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + ACCESS_TOKEN)

    response = client.get("/api/pinakes/auth/me/")
    assert response.status_code == status.HTTP_200_OK

    social_user = testuser.social_auth.get(provider="keycloak-oidc")
    assert social_user.extra_data == {
        "access_token": ACCESS_TOKEN,
        "refresh_token": REFRESH_TOKEN,
    }

    assert authenticate.call_count == 1
    assert authenticate.spy_return == (testuser, ACCESS_TOKEN)


@pytest.mark.django_db
def test_bearer_online_auth(mocker, testuser):
    authenticate = mocker.spy(
        KeycloakBearerOnlineAuthentication, "authenticate"
    )
    mocker.patch.object(
        APIView, "authentication_classes", [KeycloakBearerOnlineAuthentication]
    )

    def get_json(obj, url, **kwargs):
        if url == "<introspect>":
            return {
                "active": True,
                "audience": ["account", "pinakes"],
            }
        if url == "<userinfo>":
            return {
                "sub": USER_UID,
                "name": "Fred Sample",
                "preferred_username": "fred",
            }
        raise ValueError("Unexpected url")

    mocker.patch.multiple(
        KeycloakOpenIdConnect,
        get_json=get_json,
        oidc_config=mock.Mock(
            return_value={
                "introspection_endpoint": "<introspect>",
                "userinfo_endpoint": "<userinfo>",
            }
        ),
        JWT_ALGORITHMS=["HS256"],
    )

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + ACCESS_TOKEN)

    response = client.get("/api/pinakes/auth/me/")
    assert response.status_code == status.HTTP_200_OK

    social_user = testuser.social_auth.get(provider="keycloak-oidc")
    assert social_user.extra_data == {
        "access_token": ACCESS_TOKEN,
        "refresh_token": REFRESH_TOKEN,
    }

    assert authenticate.call_count == 1
    assert authenticate.spy_return == (testuser, ACCESS_TOKEN)
