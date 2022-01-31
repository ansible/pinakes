from unittest import mock
from urllib.error import HTTPError
import pytest
from django.conf import settings

from ansible_catalog.common.auth.keycloak import models
from ansible_catalog.common.auth.keycloak.admin import AdminClient


SERVER_URL = "https://keycloak.example.com/auth"
REALM = "testrealm"
TOKEN = "ATESTACCESSTOKEN"


@pytest.fixture
def api_client(mocker):
    client_mock = mock.Mock()
    mocker.patch(
        "ansible_catalog.common.auth.keycloak.admin.ApiClient",
        return_value=client_mock,
    )
    return client_mock


def _check_model(obj, cls, **kwargs):
    assert type(obj) is cls
    for attr, value in kwargs.items():
        assert getattr(obj, attr) == value


def test_list_groups(api_client):
    client = AdminClient(SERVER_URL, REALM, TOKEN)

    api_client.request_json.return_value = [
        {
            "id": "87bd0889-2ae0-45c5-9d27-a58b7cb728f7",
            "name": "test-group-01",
            "path": "/test-group-01",
            "clientRoles": {"catalog": ["approver", "adjuster"]},
            "subGroups": [],
        },
        {
            "id": "87bd0889-2ae0-45c5-9d27-a58b7cb728f7",
            "name": "test-group-02",
            "path": "/test-group-02",
            "subGroups": [
                {
                    "id": "5d618a85-0fe6-479a-895e-6612de58b967",
                    "name": "test-group-03",
                    "path": "/test-group-02/test-group-03",
                    "subGroups": [],
                }
            ],
        },
    ]

    groups = client.list_groups(brief_representation=False)
    params = {"briefRepresentation": False}
    api_client.request_json.assert_called_with(
        "GET",
        f"{SERVER_URL}/admin/realms/{REALM}/groups",
        params=params,
    )

    assert groups == [
        models.Group(
            id="87bd0889-2ae0-45c5-9d27-a58b7cb728f7",
            name="test-group-01",
            path="/test-group-01",
            client_roles={
                settings.KEYCLOAK_CLIENT_ID: ["approver", "adjuster"]
            },
            sub_groups=[],
        ),
        models.Group(
            id="87bd0889-2ae0-45c5-9d27-a58b7cb728f7",
            name="test-group-02",
            path="/test-group-02",
            sub_groups=[
                models.Group(
                    id="5d618a85-0fe6-479a-895e-6612de58b967",
                    name="test-group-03",
                    path="/test-group-02/test-group-03",
                    sub_groups=[],
                )
            ],
        ),
    ]


def test_iter_group_members_invalid_id(api_client):
    client = AdminClient(SERVER_URL, REALM, TOKEN)
    group_id = "does-not-exist"

    api_client.request_json.side_effect = HTTPError(
        SERVER_URL, 404, "Not Found", {}, None
    )
    with pytest.raises(HTTPError):
        list(client.iter_group_members(group_id))


def test_iter_group_members(api_client):
    client = AdminClient(SERVER_URL, REALM, TOKEN)
    group_id = "ff530978-1e4f-4bb9-a1d8-2c374c9ad739"

    api_client.request_json.side_effect = [
        [
            {
                "id": "00000000-1111-2222-3333-444444444444",
                "username": "barney",
                "email": "barney@example.com",
                "firstName": "Barney",
                "lastName": "Rubble",
            },
            {
                "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                "username": "fred",
                "email": "fred@example.com",
                "firstName": "Fred",
                "lastName": "Flintstone",
            },
        ],
        [],
    ]

    assert len(list(client.iter_group_members(group_id))) == 2


def test_list_group_members(api_client):
    client = AdminClient(SERVER_URL, REALM, TOKEN)
    group_id = "ff530978-1e4f-4bb9-a1d8-2c374c9ad739"
    first = 0
    max_prefetch = 10
    params = {"first": first, "max": max_prefetch}

    api_client.request_json.return_value = [
        {
            "id": "00000000-1111-2222-3333-444444444444",
            "username": "barney",
            "email": "barney@example.com",
            "firstName": "Barney",
            "lastName": "Rubble",
        },
        {
            "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "username": "fred",
            "email": "fred@example.com",
            "firstName": "Fred",
            "lastName": "Flintstone",
        },
    ]

    assert len(client.list_group_members(group_id, first, max_prefetch)) == 2
    api_client.request_json.assert_called_with(
        "GET",
        f"{SERVER_URL}/admin/realms/{REALM}/groups/{group_id}/members",
        params=params,
    )
