from __future__ import annotations

from typing import Optional, Tuple

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from jose import jwt
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from social_django.models import AbstractUserSocialAuth, DjangoStorage
from social_django.strategy import DjangoStrategy

from pinakes.common.auth.keycloak_oidc import KeycloakOpenIdConnect

User: AbstractUser = get_user_model()
UserTokenPair = Tuple[AbstractUser, str]


class _CustomDjangoStrategy(DjangoStrategy):
    def __init__(self, settings, storage, request=None, tpl=None):
        self._settings = settings
        super().__init__(storage, request, tpl)

    def get_setting(self, name):
        if name in self._settings:
            return self._settings[name]
        return super().get_setting(name)


class KeycloakSessionAuthentication(authentication.SessionAuthentication):
    auth_backend = KeycloakOpenIdConnect

    def authenticate(self, request: Request) -> Optional[UserTokenPair]:
        auth = super().authenticate(request)
        if auth is None:
            return None
        user = auth[0]
        return user, request.keycloak_user.access_token

    def get_social_user(
        self, request: Request
    ) -> Optional[AbstractUserSocialAuth]:
        return request.keycloak_user


class BaseKeycloakBearerAuthentication(authentication.BaseAuthentication):
    auth_scheme = "Bearer"
    auth_backend = KeycloakOpenIdConnect
    # NOTE: Use custom pipeline to disable loading extra data
    auth_pipeline = [
        "social_core.pipeline.social_auth.social_details",
        "social_core.pipeline.social_auth.social_uid",
        "social_core.pipeline.social_auth.auth_allowed",
        "social_core.pipeline.social_auth.social_user",
        "social_core.pipeline.user.get_username",
        "social_core.pipeline.user.create_user",
        "social_core.pipeline.social_auth.associate_user",
        "social_core.pipeline.user.user_details",
    ]

    def authenticate_header(self, request: Request) -> str:
        return self.auth_scheme

    def get_token(self, request: Request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        auth = auth_header.split()
        if not auth or auth[0].lower() != self.auth_scheme.lower():
            return None

        if len(auth) == 1:
            msg = _("Invalid authorization header. No credentials provided.")
            raise AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _(
                "Invalid authorization header. Credentials string should "
                "not contain spaces."
            )
            raise AuthenticationFailed(msg)
        return auth[1]

    def load_strategy(self, request: Request) -> DjangoStrategy:
        settings = {
            "SOCIAL_AUTH_PIPELINE": self.auth_pipeline,
        }
        strategy = _CustomDjangoStrategy(
            settings, DjangoStorage, request=request
        )
        return strategy


class KeycloakBearerOfflineAuthentication(BaseKeycloakBearerAuthentication):
    def authenticate(self, request: Request) -> Optional[UserTokenPair]:
        token = self.get_token(request)
        if token is None:
            return None

        strategy = self.load_strategy(request)
        backend = self.auth_backend(strategy)

        key = backend.find_valid_key(token)
        if not key:
            raise AuthenticationFailed(_("No valid JWK found."))

        client_id, _client_secret = backend.get_key_and_secret()
        try:
            payload = jwt.decode(
                token,
                key,
                algorithms=backend.JWT_ALGORITHMS,
                audience=client_id,
                issuer=backend.id_token_issuer(),
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed(_("Signature has expired."))
        except jwt.JWTClaimsError:
            raise AuthenticationFailed(_("Invalid claims."))
        except jwt.JWTError:
            raise AuthenticationFailed(_("Invalid signature."))

        user = strategy.authenticate(backend, response=payload)
        if not user:
            raise AuthenticationFailed
        return user, token


class KeycloakBearerOnlineAuthentication(BaseKeycloakBearerAuthentication):
    def authenticate(self, request: Request) -> Optional[UserTokenPair]:
        token = self.get_token(request)
        if token is None:
            return None

        strategy = self.load_strategy(request)
        backend = self.auth_backend(strategy)

        client_id, client_secret = backend.get_key_and_secret()

        introspect_url = self._introspect_url(backend)
        response = backend.get_json(
            introspect_url,
            method="POST",
            auth=(client_id, client_secret),
            data={"token": token},
        )

        self._validate_response(response, client_id)

        response = backend.user_data(token)
        user = strategy.authenticate(backend, response=response)
        if not user:
            raise AuthenticationFailed
        return user, token

    def _introspect_url(self, backend: KeycloakOpenIdConnect):
        return backend.oidc_config().get("introspection_endpoint")

    def _validate_response(self, response, client_id):
        if not response.get("active"):
            raise AuthenticationFailed(_("Token expired"))

        # Validate audience
        audience_claims = response.get("audience")
        if not audience_claims:
            raise AuthenticationFailed(_("Invalid audience"))
        if isinstance(audience_claims, str):
            audience_claims = [audience_claims]
        if client_id not in audience_claims:
            raise AuthenticationFailed(_("Invalid audience"))
