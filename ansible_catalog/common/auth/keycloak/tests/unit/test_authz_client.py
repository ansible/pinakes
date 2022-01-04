from unittest import mock

import pytest

from ansible_catalog.common.auth.keycloak import models, exceptions
from ansible_catalog.common.auth.keycloak.authz import AuthzClient
from ansible_catalog.common.auth.keycloak.common import (
    ManualUma2ConfigurationPolicy,
)


SERVER_URL = "https://keycloak.example.com/auth"
REALM = "testrealm"
CLIENT_ID = "pytest"
TOKEN = "ATESTACCESSTOKEN"


@pytest.fixture
def api_client(mocker):
    client_mock = mock.Mock()
    mocker.patch(
        "ansible_catalog.common.auth.keycloak.authz.ApiClient",
        return_value=client_mock,
    )
    return client_mock


@pytest.fixture
def authz_client(api_client):
    uma2_policy = ManualUma2ConfigurationPolicy(SERVER_URL, REALM)
    return AuthzClient(
        SERVER_URL,
        REALM,
        CLIENT_ID,
        TOKEN,
        uma2_policy,
    )


def test_get_permissions(api_client, authz_client):
    api_client.request_json.return_value = [
        {
            "rsid": "id1",
            "rsname": "test-resource-a",
            "scopes": ["scope-a", "scope-b"],
        },
        {"rsid": "id2", "rsname": "test-resource-b", "scopes": ["scope-a"]},
    ]

    permissions = authz_client.get_permissions()

    api_client.request_json.assert_called_once_with(
        "POST",
        f"{SERVER_URL}/realms/{REALM}/protocol/openid-connect/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:uma-ticket",
            "audience": CLIENT_ID,
            "response_include_resource_name": True,
            "response_mode": "permissions",
        },
    )

    assert isinstance(permissions[0], models.AuthzResource)
    assert permissions[0].rsid == "id1"
    assert permissions[0].rsname == "test-resource-a"
    assert permissions[0].scopes == ["scope-a", "scope-b"]

    assert isinstance(permissions[1], models.AuthzResource)
    assert permissions[1].rsid == "id2"
    assert permissions[1].rsname == "test-resource-b"
    assert permissions[1].scopes == ["scope-a"]


def test_get_permissions_query(api_client, authz_client):
    api_client.request_json.return_value = []

    authz_client.get_permissions(
        models.AuthzPermission("resource-a", "scope-a")
    )

    api_client.request_json.assert_called_once_with(
        "POST",
        f"{SERVER_URL}/realms/{REALM}/protocol/openid-connect/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:uma-ticket",
            "audience": CLIENT_ID,
            "response_include_resource_name": True,
            "response_mode": "permissions",
            "permission": ["resource-a#scope-a"],
        },
    )

    api_client.request_json.reset_mock()

    authz_client.get_permissions(
        [
            models.AuthzPermission("resource-a", "scope-a"),
            models.AuthzPermission("resource-b", "scope-b"),
        ]
    )

    api_client.request_json.assert_called_once_with(
        "POST",
        f"{SERVER_URL}/realms/{REALM}/protocol/openid-connect/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:uma-ticket",
            "audience": CLIENT_ID,
            "response_include_resource_name": True,
            "response_mode": "permissions",
            "permission": ["resource-a#scope-a", "resource-b#scope-b"],
        },
    )


def test_get_permissions_forbidden(api_client, authz_client):
    api_client.request_json.side_effect = exceptions.Forbidden()

    permissions = authz_client.get_permissions()

    assert permissions == []


def test_check_permissions(api_client, authz_client):
    api_client.request_json.return_value = {"result": True}

    assert (
        authz_client.check_permissions(
            models.AuthzPermission("resource-a", "scope-a")
        )
        is True
    )

    api_client.request_json.assert_called_once_with(
        "POST",
        f"{SERVER_URL}/realms/{REALM}/protocol/openid-connect/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:uma-ticket",
            "audience": CLIENT_ID,
            "response_mode": "decision",
            "permission": ["resource-a#scope-a"],
        },
    )


def test_check_permissions_negative(api_client, authz_client):
    api_client.request_json.return_value = {"result": False}

    assert (
        authz_client.check_permissions(
            models.AuthzPermission("resource-a", "scope-a")
        )
        is False
    )

    api_client.request_json.assert_called_once_with(
        "POST",
        f"{SERVER_URL}/realms/{REALM}/protocol/openid-connect/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:uma-ticket",
            "audience": CLIENT_ID,
            "response_mode": "decision",
            "permission": ["resource-a#scope-a"],
        },
    )


def test_check_permissions_forbidden(api_client, authz_client):
    api_client.request_json.side_effect = exceptions.Forbidden()

    assert (
        authz_client.check_permissions(
            models.AuthzPermission("resource-a", "scope-a")
        )
        is False
    )

    api_client.request_json.assert_called_once_with(
        "POST",
        f"{SERVER_URL}/realms/{REALM}/protocol/openid-connect/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:uma-ticket",
            "audience": CLIENT_ID,
            "response_mode": "decision",
            "permission": ["resource-a#scope-a"],
        },
    )
