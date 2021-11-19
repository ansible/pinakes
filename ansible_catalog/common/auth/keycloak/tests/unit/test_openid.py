from unittest import mock

import pytest

from ansible_catalog.common.auth.keycloak.models import OpenIDConfiguration
from ansible_catalog.common.auth.keycloak.openid import OpenIdConnect


SERVER_URL = "https://keycloak.example.com/auth"
REALM = "testrealm"
CLIENT_ID = "pytest"
CLIENT_SECRET = "supersecret"

TOKEN_ENDPOINT = f"{SERVER_URL}/realms/{REALM}/protocol/openid-connect"


@pytest.fixture
def api_client(mocker):
    client_mock = mock.Mock()
    mocker.patch(
        "ansible_catalog.common.auth.keycloak.openid.ApiClient",
        return_value=client_mock,
    )
    return client_mock


def test_openid_configuration(api_client):
    openid_client = OpenIdConnect(SERVER_URL, REALM, CLIENT_ID)

    api_client.request_json.return_value = {"token_endpoint": TOKEN_ENDPOINT}

    config = openid_client.openid_configuration()

    assert config.token_endpoint == TOKEN_ENDPOINT
    assert api_client.request_json.call_count == 1
    api_client.request_json.assert_called_with(
        "GET", f"{SERVER_URL}/realms/{REALM}/.well-known/openid-configuration"
    )

    openid_client.openid_configuration()
    assert api_client.request_json.call_count == 1

    openid_client.openid_configuration(force_reload=True)
    assert api_client.request_json.call_count == 2


def test_password_auth(api_client):
    openid_client = OpenIdConnect(SERVER_URL, REALM, CLIENT_ID)
    openid_client._openid_configuration = OpenIDConfiguration(
        token_endpoint=TOKEN_ENDPOINT
    )

    response_expected = {
        "access_token": "ATESTACCESSTOKEN",
    }
    api_client.request_json.return_value = response_expected

    response = openid_client.password_auth("fred", "fred123")

    assert response == response_expected
    api_client.request_json.assert_called_with(
        "POST",
        TOKEN_ENDPOINT,
        data={
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "username": "fred",
            "password": "fred123",
        },
    )


def test_password_auth_client_secret(api_client):
    openid_client = OpenIdConnect(SERVER_URL, REALM, CLIENT_ID, CLIENT_SECRET)
    openid_client._openid_configuration = OpenIDConfiguration(
        token_endpoint=TOKEN_ENDPOINT
    )

    response_expected = {
        "access_token": "ATESTACCESSTOKEN",
    }
    api_client.request_json.return_value = response_expected

    response = openid_client.password_auth("fred", "fred123")

    assert response == response_expected
    api_client.request_json.assert_called_with(
        "POST",
        TOKEN_ENDPOINT,
        data={
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "username": "fred",
            "password": "fred123",
        },
    )


def test_client_credentials_auth(api_client):
    openid_client = OpenIdConnect(SERVER_URL, REALM, CLIENT_ID, CLIENT_SECRET)
    openid_client._openid_configuration = OpenIDConfiguration(
        token_endpoint=TOKEN_ENDPOINT
    )

    response_expected = {
        "access_token": "ATESTACCESSTOKEN",
    }
    api_client.request_json.return_value = response_expected

    response = openid_client.client_credentials_auth()

    assert response == response_expected
    api_client.request_json.assert_called_with(
        "POST",
        TOKEN_ENDPOINT,
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
    )
