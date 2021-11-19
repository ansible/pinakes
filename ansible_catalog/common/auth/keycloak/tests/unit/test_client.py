from unittest import mock

import pytest

from ansible_catalog.common.auth.keycloak.client import ApiClient


@pytest.fixture
def session(mocker):
    session_mock = mock.Mock()
    mocker.patch("requests.Session", return_value=session_mock)
    yield session_mock


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_api_client_request(session, method):
    client = ApiClient(token="TOKENVALUE")
    client.request(method, "https://example.com/")

    session.request.assert_called_with(
        method,
        "https://example.com/",
        headers={
            "Authorization": "Bearer TOKENVALUE",
        },
        params=None,
        data=None,
        json=None,
    )


def test_api_client_request_no_token(session):
    client = ApiClient()
    client.request("GET", "https://example.com/")

    session.request.assert_called_with(
        "GET",
        "https://example.com/",
        headers={},
        params=None,
        data=None,
        json=None,
    )


def test_api_client_request_post_json(session):
    client = ApiClient()
    client.request(
        "POST",
        "https://example-2.com/",
        headers={"Accept": "application/json"},
        json={
            "foo": 1,
            "bar": 2,
        },
    )

    session.request.assert_called_with(
        "POST",
        "https://example-2.com/",
        headers={"Accept": "application/json"},
        params=None,
        data=None,
        json={"foo": 1, "bar": 2},
    )


def test_api_client_request_post_data(session):
    client = ApiClient()
    client.request(
        "POST",
        "https://example-3.com/",
        headers={"Accept": "application/json"},
        data={"foo": 1, "bar": 2},
    )

    session.request.assert_called_with(
        "POST",
        "https://example-3.com/",
        headers={"Accept": "application/json"},
        params=None,
        data={"foo": 1, "bar": 2},
        json=None,
    )


def test_api_client_request_json(session):
    client = ApiClient(token="TOKENVALUE")
    client.request_json(
        "POST",
        "https://example-4.com/",
        headers={"Content-Type": "application/json"},
        data=b'{"foo": 1, "bar": 2}',
    )

    session.request.assert_called_with(
        "POST",
        "https://example-4.com/",
        headers={
            "Authorization": "Bearer TOKENVALUE",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        params=None,
        data=b'{"foo": 1, "bar": 2}',
        json=None,
    )


def test_api_client_request_json_no_token(session):
    client = ApiClient()
    client.request_json(
        "POST",
        "https://example-5.com/",
        headers={"Content-Type": "application/json"},
        data=b'{"foo": 1, "bar": 2}',
    )

    session.request.assert_called_with(
        "POST",
        "https://example-5.com/",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        params=None,
        data=b'{"foo": 1, "bar": 2}',
        json=None,
    )


# TODO: Test exception handling
