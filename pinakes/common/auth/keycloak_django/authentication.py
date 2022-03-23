from typing import Any, Optional, Tuple

import requests
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.authentication import (
    BaseAuthentication,
    SessionAuthentication,
)
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from social_django.models import AbstractUserSocialAuth
from social_django.utils import load_strategy

from pinakes.common.auth.keycloak_oidc import KeycloakOpenIdConnect


UserTokenPair = Tuple[AbstractUser, Any]


class KeycloakSessionAuthentication(SessionAuthentication):
    social_auth_provider = "keycloak-oidc"

    def authenticate(self, request: Request) -> Optional[UserTokenPair]:
        auth = super().authenticate(request)
        if auth is None:
            return None

        user = auth[0]

        keycloak_user = self.get_social_user(user)
        strategy = load_strategy(request)
        try:
            token = keycloak_user.get_access_token(strategy)
        except requests.HTTPError as exc:
            if exc.response.status_code == status.HTTP_400_BAD_REQUEST:
                raise AuthenticationFailed(_("Access token expired"))
            raise

        if token is None:
            raise AuthenticationFailed(_("Access token is missing"))

        return user, token

    def get_social_user(
        self, user: AbstractUser
    ) -> Optional[AbstractUserSocialAuth]:
        social_auth = getattr(user, "social_auth", None)
        if social_auth is None:
            return None

        try:
            return social_auth.get(provider=self.social_auth_provider)
        except ObjectDoesNotExist:
            return None


class BaseKeycloakBearerAuthentication(BaseAuthentication):
    auth_scheme = "Bearer"
    auth_backend = KeycloakOpenIdConnect

    def authenticate_header(self, request: Request) -> str:
        return self.auth_scheme

    def get_token(self, request: Request) -> Optional[str]:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        auth = auth_header.split()
        if not auth or auth[0].lower() != self.auth_scheme.lower():
            return None

        if len(auth) == 1:
            msg = _("Invalid basic header. No credentials provided.")
            raise AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _(
                "Invalid basic header. Credentials string should "
                "not contain spaces."
            )
            raise AuthenticationFailed(msg)
        return auth[1]


class KeycloakBearerOnlineAuthentication(BaseKeycloakBearerAuthentication):
    def authenticate(self, request: Request) -> Optional[UserTokenPair]:
        token = self.get_token(request)
        if not token:
            return None

        strategy = load_strategy(request)
        backend = self.auth_backend(strategy)

        try:
            userinfo = backend.user_data(token)
        except requests.HTTPError as exc:
            if exc.response.status_code == status.HTTP_401_UNAUTHORIZED:
                raise AuthenticationFailed(_("Authentication failed."))
            raise

        user = strategy.authenticate(backend, response=userinfo)
        if user is None:
            raise AuthenticationFailed(_("Authentication failed."))

        return user, token


class KeycloakBearerOfflineAuthentication(BaseKeycloakBearerAuthentication):
    def authenticate(self, request) -> Optional[UserTokenPair]:
        # TODO(cutwater): Implementation required
        raise NotImplementedError
