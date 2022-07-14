from unittest import mock

import pytest
import requests

from pinakes.common.auth.keycloak import exceptions
from pinakes.common.auth.keycloak.client import ApiClient


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


def _mock_response_with_exception(status_code, json_data):
    response = mock.Mock()
    response.status_code = status_code
    response.json.return_value = json_data

    error = requests.HTTPError(response=response)
    response.raise_for_status.side_effect = error

    return response


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


def test_api_client_exception_not_found(session):
    client = ApiClient()
    session.request.return_value = _mock_response_with_exception(
        status_code=requests.codes.not_found, json_data={}
    )
    with pytest.raises(exceptions.NotFound) as excinfo:
        client.request_json("GET", "https://example-6.com")
    assert str(excinfo.value) == "API Error (status: 404)"


def test_api_client_exception_conflict(session):
    client = ApiClient()
    session.request.return_value = _mock_response_with_exception(
        status_code=requests.codes.conflict, json_data={}
    )
    with pytest.raises(exceptions.Conflict) as excinfo:
        client.request_json("GET", "https://example-7.com")
    assert str(excinfo.value) == "API Error (status: 409)"


def test_api_client_exception_with_error(session):
    client = ApiClient()
    session.request.return_value = _mock_response_with_exception(
        status_code=requests.codes.bad_request,
        json_data={"error": "invalid request"},
    )
    with pytest.raises(exceptions.HttpError) as excinfo:
        client.request_json("GET", "https://example-8.com")
    assert str(excinfo.value) == "invalid request (status: 400)"


def test_api_client_exception_with_error_description(session):
    client = ApiClient()
    session.request.return_value = _mock_response_with_exception(
        status_code=requests.codes.bad_request,
        json_data={
            "error": "invalid request",
            "error_description": "unknown error",
        },
    )
    with pytest.raises(exceptions.HttpError) as excinfo:
        client.request_json("GET", "https://example-9.com")
    assert str(excinfo.value) == "invalid request: unknown error (status: 400)"
