from django.conf import settings

from ansible_catalog.common.auth.keycloak.admin import (
    create_admin_client,
    AdminClient,
)


def get_admin_client() -> AdminClient:
    return create_admin_client(
        server_url=settings.KEYCLOAK_URL,
        realm=settings.KEYCLOAK_REALM,
        client_id=settings.KEYCLOAK_CLIENT_ID,
        client_secret=settings.KEYCLOAK_CLIENT_SECRET,
    )
