from django.conf import settings

from ansible_catalog.common.auth.keycloak.admin import (
    create_admin_client,
    AdminClient,
)
from ansible_catalog.common.auth.keycloak.uma import (
    create_uma_client,
    UmaClient,
)


def get_admin_client() -> AdminClient:
    return create_admin_client(
        server_url=settings.KEYCLOAK_URL,
        realm=settings.KEYCLOAK_REALM,
        client_id=settings.KEYCLOAK_CLIENT_ID,
        client_secret=settings.KEYCLOAK_CLIENT_SECRET,
    )


def get_uma_client() -> UmaClient:
    return create_uma_client(
        server_url=settings.KEYCLOAK_URL,
        realm=settings.KEYCLOAK_REALM,
        client_id=settings.KEYCLOAK_CLIENT_ID,
        client_secret=settings.KEYCLOAK_CLIENT_SECRET,
    )
