from typing import Optional

from django.contrib import auth as django_auth
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpRequest

from rest_framework import status
from social_django.models import UserSocialAuth
from social_django.utils import load_strategy

import requests


KEYCLOAK_PROVIDER = "keycloak-oidc"


class TokenRefreshError(Exception):
    pass


class KeycloakAuthMiddleware:
    __slots__ = ("get_response",)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        try:
            request.keycloak_user = self._process_keycloak_user(request.user)
        except TokenRefreshError:
            # NOTE(cutwater): Not sure about correctness of this one
            django_auth.logout(request)
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)
        return self.get_response(request)

    def _process_keycloak_user(self, user: User) -> Optional[UserSocialAuth]:
        social_auth = getattr(user, "social_auth", None)
        if social_auth is None:
            return None

        try:
            keycloak_user = social_auth.get(provider=KEYCLOAK_PROVIDER)
        except ObjectDoesNotExist:
            return None

        try:
            token = keycloak_user.get_access_token(load_strategy())
        except requests.HTTPError as e:
            if e.response.status_code == status.HTTP_400_BAD_REQUEST:
                raise TokenRefreshError("Access token expired")
            raise

        if token is None:
            raise TokenRefreshError("Access token is missing")

        return keycloak_user
