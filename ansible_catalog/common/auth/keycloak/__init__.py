from typing import Any, Tuple, Sequence
from dataclasses import dataclass

import jwt
import requests
from rest_framework import status

GRANT_TYPE = "urn:ietf:params:oauth:grant-type:uma-ticket"

PermissionsQuery = Sequence[Tuple[str, str]]


@dataclass
class Uma2Config:
    token_endpoint: str


# TODO(cutwater): Split this class into multiple clients
#   addressing common tasks.
class KeycloakClient:
    def __init__(self, realm_url: str):
        self._realm_url = realm_url.rstrip("/") + "/"
        self._client = requests.Session()

        self._uma2_config = None

    def close(self):
        self._client.close()

    @property
    def uma2_config(self) -> Uma2Config:
        if self._uma2_config is None:
            self._uma2_config = self._get_uma2_config()
        return self._uma2_config

    # TODO(cutwater): Parse permissions into structured objects
    def get_permissions(
        self, token: str, client_id: str, query: PermissionsQuery = None
    ) -> list:
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "grant_type": GRANT_TYPE,
            "audience": client_id,
            "response_include_resource_name": True,
        }
        if query:
            data["permission"] = ["#".join(p) for p in query]

        try:
            result = self._request_json(
                self.uma2_config.token_endpoint,
                method="POST",
                headers=headers,
                data=data,
            )
        except requests.HTTPError as e:
            if e.response.status_code == status.HTTP_403_FORBIDDEN:
                return []
            raise
        rpt_token = jwt.decode(
            result["access_token"], options={"verify_signature": False}
        )
        return rpt_token["authorization"]["permissions"]

    def check_permissions(
        self, token: str, client_id: str, query: PermissionsQuery
    ) -> bool:
        permissions = self.get_permissions(token, client_id, query)
        if not permissions:
            return False
        for resource, scope in query:
            for permission in permissions:
                rsname = permission["rsname"]
                scopes = permission.get("scopes", [])
                if resource == rsname and scope in scopes:
                    break
            else:
                return False
        return True

    def _get_uma2_config(self) -> Uma2Config:
        url = self._build_url(".well-known/uma2-configuration")
        data = self._request_json(url)
        return Uma2Config(token_endpoint=data["token_endpoint"])

    def _build_url(self, path: str) -> str:
        return self._realm_url + path

    def _request_json(self, url, method="GET", headers=None, data=None) -> Any:
        response = self._client.request(
            method, url, headers=headers, data=data
        )
        # TODO(cutwater): Handle exceptions
        response.raise_for_status()
        return response.json()
