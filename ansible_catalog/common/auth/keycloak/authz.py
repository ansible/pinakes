from dataclasses import dataclass
from typing import Optional, Iterable, List, Union

import jwt

from .client import ApiClient
from .common import (
    Uma2ConfigurationPolicyProto,
    DefaultUma2ConfigurationPolicy,
)
from . import constants
from . import exceptions
from . import models


PermissionsQuery = Union[
    models.AuthzPermission, Iterable[models.AuthzPermission]
]


class AuthzClient:
    def __init__(
        self,
        server_url: str,
        realm: str,
        client_id: str,
        token: str,
        uma2_policy: Optional[Uma2ConfigurationPolicyProto] = None,
    ):
        self._server_url = server_url.rstrip("/")
        self._realm = realm
        self._client_id = client_id

        self._uma2_configuration = None

        self._client = ApiClient(token=token)

        if uma2_policy is None:
            uma2_policy = DefaultUma2ConfigurationPolicy(
                server_url, realm, self._client
            )
        self._uma2_policy = uma2_policy

    def uma2_configuration(
        self, force_reload=False
    ) -> models.Uma2Configuration:
        if self._uma2_configuration is None or force_reload:
            self._uma2_configuration = self._uma2_policy.uma2_configuration()
        return self._uma2_configuration

    def get_permissions(
        self, permissions: Optional[PermissionsQuery] = None
    ) -> List[models.AuthzResource]:
        data = {
            "grant_type": constants.UMA_TICKET_GRANT,
            "audience": self._client_id,
            "response_mode": constants.AUTHZ_RESPONSE_MODE_PERMISSIONS,
            "response_include_resource_name": True,
        }
        if permissions:
            if isinstance(permissions, models.AuthzPermission):
                permissions = [permissions]
            data["permission"] = [str(p) for p in permissions]

        try:
            response = self._client.request_json(
                "POST",
                self.uma2_configuration().token_endpoint,
                data=data,
            )
        except exceptions.Forbidden:
            return []
        result = [models.AuthzResource.parse_obj(p) for p in response]
        return result

    def check_permissions(
        self, permissions: Optional[PermissionsQuery] = None
    ) -> bool:
        data = {
            "grant_type": constants.UMA_TICKET_GRANT,
            "audience": self._client_id,
            "response_mode": constants.AUTHZ_RESPONSE_MODE_DECISION,
        }
        if permissions:
            if isinstance(permissions, models.AuthzPermission):
                permissions = [permissions]
            data["permission"] = [str(p) for p in permissions]
        try:
            response = self._client.request_json(
                "POST",
                self.uma2_configuration().token_endpoint,
                data=data,
            )
        except exceptions.Forbidden:
            return False
        else:
            return response["result"]
