from unittest import mock

import pytest

from pinakes.common.auth.keycloak import models, exceptions
from pinakes.common.auth.keycloak.uma import UmaClient

SERVER_URL = "https://keycloak.example.com/auth"
REALM = "testrealm"
TOKEN = "ATESTACCESSTOKEN"

OPENID_CONNECT_URL = f"{SERVER_URL}/realms/{REALM}/protocol/openid-connect"
PROTECTION_URL = f"{SERVER_URL}/realms/{REALM}/authz/protection"

RESOURCE_REGISTRATION_ENDPOINT = f"{PROTECTION_URL}/resource_set"
PERMISSION_ENDPOINT = f"{PROTECTION_URL}/permission"
POLICY_ENDPOINT = f"{PROTECTION_URL}/policy"
TOKEN_ENDPOINT = f"{SERVER_URL}/realms/{REALM}/protocol/openid-connect"

UMA2_CONFIGURATION = models.Uma2Configuration(
    resource_registration_endpoint=RESOURCE_REGISTRATION_ENDPOINT,
    permission_endpoint=PERMISSION_ENDPOINT,
    policy_endpoint=POLICY_ENDPOINT,
    token_endpoint=TOKEN_ENDPOINT,
)


@pytest.fixture
def api_client(mocker):
    client_mock = mock.Mock()
    mocker.patch(
        "pinakes.common.auth.keycloak.uma.ApiClient",
        return_value=client_mock,
    )
    return client_mock


@pytest.fixture
def uma_client(api_client):
    client = UmaClient(SERVER_URL, REALM, TOKEN)
    client._uma2_configuration = UMA2_CONFIGURATION
    return client


def test_verify_ssl():
    session_mock = mock.Mock()
    with mock.patch("requests.Session", return_value=session_mock):
        UmaClient(
            SERVER_URL,
            REALM,
            TOKEN,
            verify_ssl="/path/to/ca/bundle",
        )

    assert session_mock.verify == "/path/to/ca/bundle"


def test_uma2_configuration(api_client):
    openid_client = UmaClient(SERVER_URL, REALM, TOKEN)

    api_client.request_json.return_value = {
        "token_endpoint": f"{OPENID_CONNECT_URL}/token",
        "introspection_endpoint": f"{OPENID_CONNECT_URL}/token/introspect",
        "end_session_endpoint": f"{OPENID_CONNECT_URL}/logout",
        "resource_registration_endpoint": RESOURCE_REGISTRATION_ENDPOINT,
        "permission_endpoint": PERMISSION_ENDPOINT,
        "policy_endpoint": POLICY_ENDPOINT,
    }

    config = openid_client.uma2_configuration()

    assert (
        config.resource_registration_endpoint == RESOURCE_REGISTRATION_ENDPOINT
    )
    assert config.permission_endpoint == PERMISSION_ENDPOINT
    assert config.policy_endpoint == POLICY_ENDPOINT

    assert api_client.request_json.call_count == 1
    api_client.request_json.assert_called_with(
        "GET", f"{SERVER_URL}/realms/{REALM}/.well-known/uma2-configuration"
    )

    openid_client.uma2_configuration()
    assert api_client.request_json.call_count == 1

    openid_client.uma2_configuration(force_reload=True)
    assert api_client.request_json.call_count == 2


def test_create_resource(api_client: mock.Mock, uma_client: UmaClient):
    resource = models.Resource(
        name="test-resource-1",
        type="test:resource",
        display_name="Test Resource 1",
        uris=[
            "https://example.com/api/v1/test-resource-1",
        ],
        scopes=["test:resource:edit", "test:resource:delete"],
    )

    api_client.request_json.return_value = {
        "_id": "id000001",
        "type": resource.type,
        "uris": resource.uris,
        "scopes": resource.scopes,
        "displayName": resource.display_name,
    }

    resource = uma_client.create_resource(resource)

    assert resource.id == "id000001"

    api_client.request_json.assert_called_once_with(
        "POST",
        RESOURCE_REGISTRATION_ENDPOINT,
        json={
            "name": "test-resource-1",
            "type": "test:resource",
            "displayName": "Test Resource 1",
            "uris": [
                "https://example.com/api/v1/test-resource-1",
            ],
            "scopes": [
                {"name": "test:resource:edit"},
                {"name": "test:resource:delete"},
            ],
        },
    )


def test_update_resource(api_client: mock.Mock, uma_client: UmaClient):
    resource = models.Resource(
        id="id000001",
        name="test-resource-1",
        type="test:resource",
        display_name="Test Resource 1",
        uris=[
            "https://example.com/api/v1/test-resource-1",
        ],
        scopes=["test:resource:edit", "test:resource:delete"],
    )

    uma_client.update_resource(resource)

    api_client.request.assert_called_once_with(
        "PUT",
        f"{RESOURCE_REGISTRATION_ENDPOINT}/id000001",
        json={
            "_id": "id000001",
            "name": "test-resource-1",
            "type": "test:resource",
            "displayName": "Test Resource 1",
            "uris": [
                "https://example.com/api/v1/test-resource-1",
            ],
            "scopes": [
                {"name": "test:resource:edit"},
                {"name": "test:resource:delete"},
            ],
        },
    )


def test_delete_resource(api_client: mock.Mock, uma_client: UmaClient):
    uma_client.delete_resource("id000001")

    api_client.request.assert_called_once_with(
        "DELETE",
        f"{RESOURCE_REGISTRATION_ENDPOINT}/id000001",
    )


def test_get_resource_by_id(api_client: mock.Mock, uma_client: UmaClient):
    api_client.request_json.return_value = {
        "_id": "id000001",
        "type": "test:resource",
        "displayName": "Test Resource 1",
        "scopes": [
            {"name": "test:resource:edit"},
            {"name": "test:resource:delete"},
        ],
    }

    resource = uma_client.get_resource_by_id("id000001")

    assert resource.id == "id000001"
    assert resource.type == "test:resource"
    assert resource.display_name == "Test Resource 1"


def test_create_permission(api_client: mock.Mock, uma_client: UmaClient):
    permission = models.UmaPermission(
        name="permission01",
        groups=["/test-group-A"],
        scopes=["test:resource:edit"],
    )

    api_client.request_json.return_value = {
        "id": "id100001",
        "name": "permission01",
        "groups": ["/test-group-A"],
        "scopes": ["test:resource:edit"],
    }

    permission = uma_client.create_permission("id000001", permission)

    assert permission.id == "id100001"

    api_client.request_json.assert_called_once_with(
        "POST",
        f"{POLICY_ENDPOINT}/id000001",
        json={
            "name": "permission01",
            "groups": ["/test-group-A"],
            "scopes": ["test:resource:edit"],
        },
    )


def test_update_permission(api_client: mock.Mock, uma_client: UmaClient):
    permission = models.UmaPermission(
        id="id100001",
        name="permission01",
        groups=["/test-group-A"],
        scopes=["test:resource:edit"],
    )

    uma_client.update_permission(permission)

    api_client.request.assert_called_once_with(
        "PUT",
        f"{POLICY_ENDPOINT}/id100001",
        json={
            "id": "id100001",
            "name": "permission01",
            "groups": ["/test-group-A"],
            "scopes": ["test:resource:edit"],
        },
    )


def test_delete_permission(api_client: mock.Mock, uma_client: UmaClient):
    uma_client.delete_permission("id000001")

    api_client.request.assert_called_once_with(
        "DELETE",
        f"{POLICY_ENDPOINT}/id000001",
    )


def test_get_permission_by_name(api_client: mock.Mock, uma_client: UmaClient):
    api_client.request_json.return_value = [
        {
            "id": "id100001",
            "name": "permission01",
            "groups": ["/test-group-A"],
            "scopes": ["test:resource:edit"],
        }
    ]

    permission = uma_client.get_permission_by_name("permission01")

    api_client.request_json.assert_called_once_with(
        "GET",
        POLICY_ENDPOINT,
        params={"name": "permission01"},
    )

    assert permission.id == "id100001"
    assert permission.name == "permission01"
    assert permission.groups == ["/test-group-A"]
    assert permission.scopes == ["test:resource:edit"]


def test_get_permission_by_name_not_found(
    api_client: mock.Mock, uma_client: UmaClient
):
    api_client.request_json.return_value = []

    with pytest.raises(exceptions.NoResultFound):
        uma_client.get_permission_by_name("permission01")


def test_get_permission_by_name_multiple_results(
    api_client: mock.Mock, uma_client: UmaClient
):
    api_client.request_json.return_value = [{}, {}]

    with pytest.raises(exceptions.MultipleResultsFound):
        uma_client.get_permission_by_name("permission01")


def find_permissions_by_name(api_client: mock.Mock, uma_client: UmaClient):
    api_client.request_json.return_value = [
        {
            "id": "id100001",
            "name": "permission01",
            "groups": ["/test-group-A"],
            "scopes": ["test:resource:edit"],
        }
    ]

    permission = uma_client.find_permissions_by_name("permission01")

    api_client.request_json.assert_called_once_with(
        "GET",
        POLICY_ENDPOINT,
        params={"name": "permission01"},
    )

    assert len(permission) == 1

    assert permission[0].id == "id100001"
    assert permission[0].name == "permission01"
    assert permission[0].groups == ["/test-group-A"]
    assert permission[0].scopes == ["test:resource:edit"]


def find_permissions_by_resource(api_client: mock.Mock, uma_client: UmaClient):
    api_client.request_json.return_value = [
        {
            "id": "id100001",
            "name": "permission01",
            "groups": ["/test-group-A"],
            "scopes": ["test:resource:edit"],
        }
    ]

    permission = uma_client.find_permissions_by_resource("id000001")

    api_client.request_json.assert_called_once_with(
        "GET",
        POLICY_ENDPOINT,
        params={"resource_id": "id000001"},
    )

    assert len(permission) == 1

    assert permission[0].id == "id100001"
    assert permission[0].name == "permission01"
    assert permission[0].groups == ["/test-group-A"]
    assert permission[0].scopes == ["test:resource:edit"]
