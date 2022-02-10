from django.conf import settings

from automation_services_catalog.common.auth.keycloak.admin import (
    create_admin_client,
    AdminClient,
)
from automation_services_catalog.common.auth.keycloak.authz import AuthzClient
from automation_services_catalog.common.auth.keycloak.uma import (
    create_uma_client,
    UmaClient,
)
from automation_services_catalog.common.auth.keycloak.common import (
    ManualUma2ConfigurationPolicy,
)


def get_admin_client() -> AdminClient:
    return create_admin_client(
        server_url=settings.KEYCLOAK_URL,
        realm=settings.KEYCLOAK_REALM,
        client_id=settings.KEYCLOAK_CLIENT_ID,
        client_secret=settings.KEYCLOAK_CLIENT_SECRET,
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
    )
