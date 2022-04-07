"""Keycloak OpenID Connect."""
import logging

import requests
from social_core.backends.open_id_connect import OpenIdConnectAuth


# TODO(cutwater): Probably better logger name required
logger = logging.getLogger("pinakes")


class KeycloakOpenIdConnect(OpenIdConnectAuth):
    """Keycloak OpenID Connect backend.

    Keycloak setup:

    1. Create a new Keycloak client in the Clients section.

    2. Configure the following parameters in the Client setup:

        Clients >

            Settings >
                Client ID (copy to settings as `KEY` value)

            Settings >
                Access Type >
                    confidential

            Credentials >
                Client Authenticator >
                    Secret (copy to settings as `SECRET` value)

    3. (optional) If the Keycloak uses different hostname configuration
        for external and internal requests, configure the frontend URL in
        the realm settings:

        Realm Settings >
            Frontend URL >
                https://sso.example.com/auth/

    Example Django settings:

    SOCIAL_AUTH_KEYCLOAK_OIDC_KEY = 'example'
    SOCIAL_AUTH_KEYCLOAK_OIDC_SECRET = '1234abcd-1234-abcd-1234-abcd1234adcd'
    SOCIAL_AUTH_KEYCLOAK_OIDC_API_URL = \
        'https://sso.example.com/auth/realms/example'
    """

    name = "keycloak-oidc"
    EXTRA_DATA = [
        *OpenIdConnectAuth.EXTRA_DATA,
        ("expires_in", "expires"),
    ]

    @property
    def OIDC_ENDPOINT(self):
        return self.setting("API_URL")

    def request(self, *args, **kwargs):
        try:
            return super().request(*args, **kwargs)
        except requests.HTTPError as exc:
            request: requests.Request = exc.request
            response: requests.Response = exc.response

            try:
                data = response.json()
            except ValueError:
                data = {}

            detail = "[{}]".format(data.get("error", "<unknown>"))
            if error_description := data.get("error_description", ""):
                detail += f" {error_description}"

            msg = (
                f"{type(exc).__name__}: {request.method} {response.url} "
                f"{response.status_code} {response.reason} "
                f"{detail}"
            )
            logger.error(msg)
            raise
