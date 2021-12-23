from __future__ import annotations

from ansible_catalog.common.auth.keycloak import models, constants
from ansible_catalog.common.auth.keycloak.client import ApiClient


class Uma2ConfigurationPolicyProto:
    def uma2_configuration(self) -> models.Uma2Configuration:
        ...


class DefaultUma2ConfigurationPolicy(Uma2ConfigurationPolicyProto):
    def __init__(
        self,
        server_url: str,
        realm: str,
        api_client: ApiClient,
    ):
        self._server_url = server_url
        self._realm = realm
        self._client = api_client

    def uma2_configuration(self) -> models.Uma2Configuration:
        path = constants.UMA2_CONFIGURATION_PATH.format(realm=self._realm)
        data = self._client.request_json("GET", f"{self._server_url}/{path}")
        return models.Uma2Configuration.parse_obj(data)


class ManualUma2ConfigurationPolicy(Uma2ConfigurationPolicyProto):
    # fmt: off
    endpoints = {
        "token_endpoint": constants.TOKEN_ENDPOINT,
        "resource_registration_endpoint":
            constants.RESOURCE_REGISTRATION_ENDPOINT,
        "permission_endpoint": constants.PERMISSION_ENDPOINT,
        "policy_endpoint": constants.POLICY_ENDPOINT,
    }
    # fmt: on

    def __init__(self, server_url: str, realm: str):
        self._server_url = server_url
        self._realm = realm

    def _make_url(self, path):
        path = path.format(realm=self._realm)
        return f"{self._server_url}/{path}"

    def uma2_configuration(self) -> models.Uma2Configuration:
        endpoints = {
            name: self._make_url(path) for name, path in self.endpoints.items()
        }
        return models.Uma2Configuration.parse_obj(endpoints)
