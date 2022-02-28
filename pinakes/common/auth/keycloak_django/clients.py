from django.conf import settings

from pinakes.common.auth.keycloak.admin import (
    create_admin_client,
    AdminClient,
)
from pinakes.common.auth.keycloak.authz import AuthzClient
from pinakes.common.auth.keycloak.openid import OpenIdConnect
from pinakes.common.auth.keycloak.uma import (
    create_uma_client,
    UmaClient,
)
from pinakes.common.auth.keycloak.common import (
    ManualUma2ConfigurationPolicy,
)


__all__ = (
    "get_admin_client",
    "get_uma_client",
    "get_authz_client",
    "get_oidc_client",
)


def get_admin_client() -> AdminClient:
    return create_admin_client(
        server_url=settings.KEYCLOAK_URL,
        realm=settings.KEYCLOAK_REALM,
        client_id=settings.KEYCLOAK_CLIENT_ID,
        client_secret=settings.KEYCLOAK_CLIENT_SECRET,
        verify_ssl=settings.KEYCLOAK_VERIFY_SSL,
    )


def get_uma_client() -> UmaClient:
    server_url = settings.KEYCLOAK_URL
    realm = settings.KEYCLOAK_REALM
    return create_uma_client(
        server_url=settings.KEYCLOAK_URL,
        realm=settings.KEYCLOAK_REALM,
        client_id=settings.KEYCLOAK_CLIENT_ID,
        client_secret=settings.KEYCLOAK_CLIENT_SECRET,
        uma2_policy=ManualUma2ConfigurationPolicy(server_url, realm),
        verify_ssl=settings.KEYCLOAK_VERIFY_SSL,
    )


def get_authz_client(access_token: str) -> AuthzClient:
    server_url = settings.KEYCLOAK_URL
    realm = settings.KEYCLOAK_REALM
    return AuthzClient(
        server_url=server_url,
        realm=realm,
        client_id=settings.KEYCLOAK_CLIENT_ID,
        token=access_token,
        uma2_policy=ManualUma2ConfigurationPolicy(server_url, realm),
        verify_ssl=settings.KEYCLOAK_VERIFY_SSL,
    )


def get_oidc_client() -> OpenIdConnect:
    oidc_client = OpenIdConnect(
        settings.KEYCLOAK_URL,
        settings.KEYCLOAK_REALM,
        settings.KEYCLOAK_CLIENT_ID,
        settings.KEYCLOAK_CLIENT_SECRET,
        verify_ssl=settings.KEYCLOAK_VERIFY_SSL,
    )
    return oidc_client
