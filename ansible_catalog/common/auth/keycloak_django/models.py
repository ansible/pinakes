from __future__ import annotations

from typing import Sequence

from django.db import models

from .utils import make_scope


class AbstractKeycloakResource(models.Model):
    KEYCLOAK_TYPE = None
    KEYCLOAK_ACTIONS = None

    keycloak_id = models.CharField(max_length=255, null=True)

    class Meta:
        abstract = True

    def keycloak_type(self) -> str:
        if not self.KEYCLOAK_TYPE:
            raise ValueError("KEYCLOAK_TYPE not defined")
        return self.KEYCLOAK_TYPE

    def keycloak_actions(self) -> Sequence[str]:
        if not self.KEYCLOAK_ACTIONS:
            raise ValueError("KEYCLOAK_ACTIONS not defined")
        return self.KEYCLOAK_ACTIONS

    def keycloak_scopes(
        self,
    ) -> Sequence[str]:
        """Returns list of keycloak scopes."""
        return [
            make_scope(self, action, validate=False)
            for action in self.keycloak_actions()
        ]

    def keycloak_name(self) -> str:
        type_ = self.keycloak_type()
        return f"{type_}:{self.pk}"
