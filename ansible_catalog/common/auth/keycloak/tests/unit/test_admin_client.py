from unittest import mock

import pytest

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

    groups = client.list_groups()

    api_client.request_json.assert_called_with(
        "GET", f"{SERVER_URL}/admin/realms/{REALM}/groups"
    )

    assert groups == [
        models.Group(
            id="87bd0889-2ae0-45c5-9d27-a58b7cb728f7",
            name="test-group-01",
            path="/test-group-01",
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
