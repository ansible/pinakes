from __future__ import annotations

from typing import Any, Optional, Union

from . import constants
from . import models
from .client import ApiClient


class OpenIdConnect:
    def __init__(
        self,
        server_url: str,
        realm: str,
        client_id: str,
        client_secret: Optional[str] = None,
        *,
        verify_ssl: Union[bool, str] = True,
    ):
        self._server_url = server_url.rstrip("/")
        self._realm = realm
        self._client_id = client_id
        self._client_secret = client_secret

        self._openid_configuration = None

        self._client = ApiClient(verify_ssl=verify_ssl)

    def openid_configuration(
        self, force_reload=False
    ) -> models.OpenIDConfiguration:
        if self._openid_configuration is None or force_reload:
            path = constants.OPENID_CONFIGURATION_PATH.format(
                realm=self._realm
            )
            data = self._client.request_json(
                "GET", f"{self._server_url}/{path}"
            )
            self._openid_configuration = models.OpenIDConfiguration.parse_obj(
                data
            )
        return self._openid_configuration

    def password_auth(self, username: str, password: str) -> Any:
        data = {
            "grant_type": constants.PASSWORD_GRANT,
            "client_id": self._client_id,
            "username": username,
            "password": password,
        }
        if self._client_secret:
            data["client_secret"] = self._client_secret
        return self._client.request_json(
            "POST",
            self.openid_configuration().token_endpoint,
            data=data,
        )

    def client_credentials_auth(self) -> Any:
        data = {
            "grant_type": constants.CLIENT_CREDENTIALS_GRANT,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        return self._client.request_json(
            "POST",
            self.openid_configuration().token_endpoint,
            data=data,
        )

    def logout_user_session(self, access_token, refresh_token) -> None:
        # TODO(cutwater): Use openid_configuration helper class.
        path = constants.END_SESSION_ENDPOINT.format(realm=self._realm)
        url = f"{self._server_url}/{path}"
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        data = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "refresh_token": refresh_token,
        }
        # REVIEW(cutwater): Why this method returns underlying Response object?
        return self._client.request("POST", url, headers=headers, data=data)
