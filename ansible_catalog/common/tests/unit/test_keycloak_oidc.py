import json

from social_core.tests.backends.oauth import OAuth2Test
from social_core.tests.backends.open_id_connect import OpenIdConnectTestMixin


class TestKeycloakOpenIdConnect(OpenIdConnectTestMixin, OAuth2Test):
    _base_url = (
        "https://keycloak.example.com/auth/realms/test/protocol/openid-connect"
    )
    backend_path = "ansible_catalog.common.auth.keycloak_oidc.KeycloakOpenIdConnect"
    issuer = "https://keycloak.example.com/auth/realms/test"
    openid_config_body = json.dumps(
        {
            "issuer": "https://keycloak.example.com/auth/realms/test",
            "authorization_endpoint": f"{_base_url}/auth",
            "token_endpoint": f"{_base_url}/token",
            "userinfo_endpoint": f"{_base_url}/userinfo",
            "end_session_endpoint": f"{_base_url}/logout",
            "revocation_endpoint": f"{_base_url}/revoke",
            "jwks_uri": f"{_base_url}/certs",
            "response_types_supported": [
                "code",
                "none",
                "id_token",
                "token",
                "id_token token",
                "code id_token",
                "code token",
                "code id_token token",
            ],
            "subject_types_supported": [
                "public",
            ],
            "id_token_signing_alg_values_supported": [
                "RS256",
            ],
            "scopes_supported": [
                "openid",
                "email",
                "profile",
            ],
            "token_endpoint_auth_methods_supported": [
                "private_key_jwt",
                "client_secret_basic",
                "client_secret_post",
                "tls_client_auth",
                "client_secret_jwt",
            ],
            "claims_supported": [
                "aud",
                "sub",
                "iss",
                "auth_time",
                "name",
                "given_name",
                "family_name",
                "preferred_username",
                "email",
                "acr",
            ],
        }
    )

    def extra_settings(self):
        settings = super().extra_settings()
        settings[
            "SOCIAL_AUTH_KEYCLOAK_OIDC_API_URL"
        ] = "https://keycloak.example.com/auth/realms/test"
        return settings
