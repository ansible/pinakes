from __future__ import annotations

from typing import List, Optional, Union

from . import exceptions
from . import models
from . import openid
from .client import ApiClient
from .common import (
    Uma2ConfigurationPolicyProto,
    DefaultUma2ConfigurationPolicy,
)


class UmaClient:
    def __init__(
        self,
        server_url: str,
        realm: str,
        token: str,
        *,
        uma2_policy: Optional[Uma2ConfigurationPolicyProto] = None,
        verify_ssl: Union[bool, str] = True,
    ):
        self._server_url = server_url.rstrip("/")
        self._realm = realm

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

    # Protection / Resource API
    def create_resource(self, resource: models.Resource) -> models.Resource:
        url = self.uma2_configuration().resource_registration_endpoint
        data = resource.dict(by_alias=True, exclude_unset=True)
        result = self._client.request_json("POST", url, json=data)
        return models.Resource.parse_obj(result)

    def update_resource(self, resource: models.Resource) -> None:
        url = "{endpoint}/{resource_id}".format(
            endpoint=self.uma2_configuration().resource_registration_endpoint,
            resource_id=resource.id,
        )
        data = resource.dict(by_alias=True, exclude_unset=True)
        self._client.request("PUT", url, json=data)

    def delete_resource(self, resource_id: str) -> None:
        url = "{endpoint}/{resource_id}".format(
            endpoint=self.uma2_configuration().resource_registration_endpoint,
            resource_id=resource_id,
        )
        self._client.request("DELETE", url)

    def get_resource_by_id(self, resource_id: str):
        url = "{endpoint}/{resource_id}".format(
            endpoint=self.uma2_configuration().resource_registration_endpoint,
            resource_id=resource_id,
        )
        result = self._client.request_json("GET", url)
        return models.Resource.parse_obj(result)

    def create_permission(
        self, resource_id: str, permission: models.UmaPermission
    ) -> models.UmaPermission:
        url = "{endpoint}/{resource_id}".format(
            endpoint=self.uma2_configuration().policy_endpoint,
            resource_id=resource_id,
        )
        data = permission.dict(by_alias=True, exclude_unset=True)
        result = self._client.request_json("POST", url, json=data)
        return models.UmaPermission(**result)

    def update_permission(self, permission: models.UmaPermission) -> None:
        url = "{endpoint}/{permission_id}".format(
            endpoint=self.uma2_configuration().policy_endpoint,
            permission_id=permission.id,
        )
        data = permission.dict(by_alias=True, exclude_unset=True)
        self._client.request("PUT", url, json=data)

    def delete_permission(self, permission_id: str) -> None:
        url = "{endpoint}/{permission_id}".format(
            endpoint=self.uma2_configuration().policy_endpoint,
            permission_id=permission_id,
        )
        self._client.request("DELETE", url)

    def get_permission_by_name(self, name: str) -> models.UmaPermission:
        permissions = self._find_permissions(name=name)
        if not permissions:
            raise exceptions.NoResultFound
        if len(permissions) > 1:
            raise exceptions.MultipleResultsFound
        return permissions[0]

    def find_permissions_by_name(
        self, name: str
    ) -> List[models.UmaPermission]:
        return self._find_permissions(name=name)

    def find_permissions_by_resource(
        self, resource_id: str
    ) -> List[models.UmaPermission]:
        return self._find_permissions(resource=resource_id)

    def _find_permissions(self, **kwargs) -> List[models.UmaPermission]:
        url = self.uma2_configuration().policy_endpoint
        result = self._client.request_json("GET", url, params=kwargs)
        return [models.UmaPermission.parse_obj(item) for item in result]


def create_uma_client(
    server_url: str,
    realm: str,
    client_id: str,
    client_secret: str,
    *,
    uma2_policy: Optional[Uma2ConfigurationPolicyProto] = None,
    verify_ssl: Union[bool, str] = True,
) -> UmaClient:
    oidc_client = openid.OpenIdConnect(
        server_url, realm, client_id, client_secret, verify_ssl=verify_ssl
    )
    token_info = oidc_client.client_credentials_auth()
    return UmaClient(
        server_url,
        realm,
        token_info["access_token"],
        uma2_policy=uma2_policy,
        verify_ssl=verify_ssl,
    )
