from typing import Optional, Sequence

from django.conf import settings
from django.db import models

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


class KeycloakResourceModel(models.Model):

    KEYCLOAK_TYPE = "unknown"
    KEYCLOAK_SCOPES = ()

    keycloak_id = models.CharField(max_length=255, null=True)

    class Meta:
        abstract = True

    @classmethod
    def keycloak_type(cls) -> str:
        return cls.KEYCLOAK_TYPE

    @classmethod
    def keycloak_scopes(
        cls,
        fully_qualified: bool = False,
        scopes: Optional[Sequence[str]] = None,
    ) -> Sequence[str]:
        """Returns list of keycloak scopes.

        If fully_qualified is set to True, prepends a resource type
        to scope names (e.g. {type}:{scope}).
        """

        if scopes is not None and not fully_qualified:
            raise ValueError("scopes argument requires fully_qualified=True")

        scopes = scopes or cls.KEYCLOAK_SCOPES

        if fully_qualified:
            type_ = cls.keycloak_type()
            return [f"{type_}:{scope}" for scope in scopes]
        else:
            return scopes

    def keycloak_name(self) -> str:
        type_ = self.keycloak_type()
        return f"{type_}:{self.pk}"
