from __future__ import annotations

from typing import Any

import requests

from . import exceptions
from .schema import Uma2Configuration, Resource, UmaPermission


class AuthzClient:
    def __init__(self, server_url: str, realm: str):
        self.server_url = server_url.rstrip("/")
        self.realm = realm

        self._session = requests.Session()

    def uma2_configuration(self) -> Uma2Configuration:
        url = (
            f"{self.server_url}/realms/{self.realm}"
            f"/.well-known/uma2-configuration"
        )
        data = self._request_json("GET", url)
        return Uma2Configuration(**data)

    # Login API
    def login(self, username: str, password: str, client_id: str, client_secret: str):
        url = self.uma2_configuration().token_endpoint
        data = {
            "grant_type": "password",
            "username": username,
            "password": password,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        data = self._request_json("POST", url, data=data)
        return data["access_token"]

    def service_login(self, client_id: str, client_secret: str) -> str:
        url = self.uma2_configuration().token_endpoint
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
        data = self._request_json("POST", url, data=data)
        return data["access_token"]

    # Authorization API
    def get_permissions(self):
        raise NotImplementedError

    def check_permissions(self):
        raise NotImplementedError

    # Protection / Resource API
    def create_resource(self, resource: Resource, token: str) -> Resource:
        url = self.uma2_configuration().resource_registration_endpoint
        headers = {"Authorization": f"Bearer {token}"}
        data = resource.dict(by_alias=True, exclude_unset=True)

        data = self._request_json("POST", url, headers=headers, json=data)
        return Resource(**data)

    def update_resource(self, resource: Resource, token: str) -> None:
        endpoint = self.uma2_configuration().resource_registration_endpoint
        url = f"{endpoint}/{resource.id}"
        headers = {"Authorization": f"Bearer {token}"}
        data = resource.dict(by_alias=True, exclude_unset=True)

        self._request("PUT", url, headers=headers, json=data)

    def delete_resource(self, resource_id: str, token: str) -> None:
        endpoint = self.uma2_configuration().resource_registration_endpoint
        url = f"{endpoint}/{resource_id}"
        headers = {"Authorization": f"Bearer {token}"}

        self._request("DELETE", url, headers=headers)

    def get_resource_by_id(self, resource_id: str, token: str):
        endpoint = self.uma2_configuration().resource_registration_endpoint
        url = f"{endpoint}/{resource_id}"
        headers = {"Authorization": f"Bearer {token}"}

        data = self._request_json("GET", url, headers=headers)
        return Resource(**data)

    def create_permission(
        self, respource_id: str, permission: UmaPermission, token: str
    ) -> UmaPermission:
        endpoint = self.uma2_configuration().policy_endpoint
        url = f"{endpoint}/{respource_id}"
        headers = {"Authorization": f"Bearer {token}"}
        data = permission.dict(by_alias=True, exclude_unset=True)

        response_data = self._request_json(
            "POST", url, headers=headers, json=data
        )
        return UmaPermission(**response_data)

    def update_permission(self, permission: UmaPermission, token: str) -> None:
        endpoint = self.uma2_configuration().policy_endpoint
        url = f"{endpoint}/{permission.id}"
        headers = {"Authorization": f"Bearer {token}"}
        data = permission.dict(by_alias=True, exclude_unset=True)

        self._request("PUT", url, headers=headers, json=data)

    def delete_permission(self, permission_id: str, token: str) -> None:
        endpoint = self.uma2_configuration().policy_endpoint
        url = f"{endpoint}/{permission_id}"
        headers = {"Authorization": f"Bearer {token}"}

        self._request("GET", url, headers=headers)

    def _request(
        self,
        method: str,
        url: str,
        *,
        headers: Any = None,
        data: Any = None,
        json: Any = None,
    ) -> requests.Response:
        response = self._session.request(
            method, url, headers=headers, data=data, json=json
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            if 400 <= exc.response.status_code < 500:
                try:
                    data = response.json()
                except ValueError:
                    raise exceptions.KeycloakError(
                        "Unexpected payload"
                    ) from exc
                raise exceptions.KeycloakRequestError(
                    error=data.get("error"),
                    error_description=data.get("error_description"),
                ) from exc
            raise exceptions.KeycloakError(str(exc)) from exc
        return response

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        headers: Any = None,
        data: Any = None,
        json: Any = None,
    ) -> Any:
        response = self._request(
            method, url, headers=headers, data=data, json=json
        )
        try:
            return response.json()
        except ValueError as exc:
            raise exceptions.KeycloakError("Unexpected payload") from exc
