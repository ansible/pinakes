from __future__ import annotations

from typing import Sequence

from django.db import models

from .utils import make_scope_name


class KeycloakMixin:
    KEYCLOAK_TYPE = None

    @classmethod
    def keycloak_type(cls) -> str:
        if not cls.KEYCLOAK_TYPE:
            raise ValueError("KEYCLOAK_TYPE not defined")
        return cls.KEYCLOAK_TYPE


class AbstractKeycloakResource(KeycloakMixin, models.Model):
    KEYCLOAK_ACTIONS = None

    keycloak_id = models.CharField(max_length=255, null=True)

    class Meta:
        abstract = True

    @classmethod
    def keycloak_actions(cls) -> Sequence[str]:
        if not cls.KEYCLOAK_ACTIONS:
            raise ValueError("KEYCLOAK_ACTIONS not defined")
        return cls.KEYCLOAK_ACTIONS

    @classmethod
    def keycloak_scopes(cls) -> Sequence[str]:
        """Returns list of keycloak scopes."""
        type_ = cls.keycloak_type()
        return [
            make_scope_name(type_, action) for action in cls.keycloak_actions()
        ]

    def keycloak_name(self) -> str:
        type_ = self.keycloak_type()
        return f"{type_}:{self.pk}"
