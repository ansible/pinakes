from typing import Optional, Iterable, List, Union, Any, Dict

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
        token: Optional[str] = True,
        *,
        uma2_policy: Optional[Uma2ConfigurationPolicyProto] = None,
        verify_ssl: Union[bool, str] = True,
    ):
        self._server_url = server_url.rstrip("/")
        self._realm = realm
        self._client_id = client_id

        self._uma2_configuration = None

        self._client = ApiClient(token=token, verify_ssl=verify_ssl)

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
        params = {
            "response_mode": constants.AUTHZ_RESPONSE_MODE_PERMISSIONS,
            "response_include_resource_name": True,
        }
        try:
            response = self._request_permissions(permissions, params)
        except exceptions.Forbidden:
            return []

        result = [models.AuthzResource.parse_obj(p) for p in response]
        return result

    def check_permissions(
        self, permissions: Optional[PermissionsQuery] = None
    ) -> bool:
        params = {"response_mode": constants.AUTHZ_RESPONSE_MODE_DECISION}
        try:
            response = self._request_permissions(permissions, params)
        except exceptions.Forbidden:
            return False

        return response["result"]

    def _request_permissions(
        self,
        permissions: Optional[PermissionsQuery],
        params: Dict[str, Any],
    ) -> Any:
        data = {
            "grant_type": constants.UMA_TICKET_GRANT,
            "audience": self._client_id,
            **params,
        }
        if permissions:
            if isinstance(permissions, models.AuthzPermission):
                permissions = [permissions]
            data["permission"] = [str(p) for p in permissions]
        return self._client.request_json(
            "POST",
            self.uma2_configuration().token_endpoint,
            data=data,
        )
