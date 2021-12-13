from unittest import mock

import pytest
import requests
from ansible_catalog.common.auth.keycloak.client import ApiClient
from ansible_catalog.common.auth.keycloak.exceptions import (
    ApiException,
    ResourceNotFound,
    ResourceExists,
)


@pytest.fixture
def session(mocker):
    session_mock = mock.Mock()
    mocker.patch("requests.Session", return_value=session_mock)
    yield session_mock


def _mock_response_with_exception(status, json_data):
    e = requests.HTTPError("error")
    e.response = mock.Mock()
    e.response.status_code = status
    e.response.json.return_value = json_data
    mock_resp = mock.Mock()
    mock_resp.raise_for_status.side_effect = e
    mock_resp.status_code = status
    return mock_resp


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


def test_api_client_request_json_404_exception(session):
    client = ApiClient()
    session.request.return_value = _mock_response_with_exception(
        status=requests.codes.not_found, json_data={}
    )
    with pytest.raises(ResourceNotFound) as execinfo:
        client.request(
            "GET",
            "https://example-6.com/",
        )


def test_api_client_request_409_exception(session):
    client = ApiClient()
    session.request.return_value = _mock_response_with_exception(
        status=requests.codes.conflict, json_data={}
    )
    with pytest.raises(ResourceExists) as execinfo:
        client.request(
            "GET",
            "https://example-7.com/",
        )


def test_api_client_request_api_exception_with_description(session):
    client = ApiClient()
    keycloak_error = {
        "error": "invalid request",
        "error_description": "no refresh token",
    }

    session.request.return_value = _mock_response_with_exception(
        status=requests.codes.bad_request, json_data=keycloak_error
    )
    with pytest.raises(ApiException) as execinfo:
        client.request(
            "GET",
            "https://example-8.com/test",
        )

    assert str(execinfo.value) == "invalid request: no refresh token"


def test_api_client_request_api_exception(session):
    client = ApiClient()
    keycloak_error = {"error": "invalid request"}

    session.request.return_value = _mock_response_with_exception(
        status=requests.codes.bad_request, json_data=keycloak_error
    )
    with pytest.raises(ApiException) as execinfo:
        client.request(
            "GET",
            "https://example-9.com/test",
        )

    assert str(execinfo.value) == "invalid request"


def test_api_client_request_api_exception_no_details(session):
    client = ApiClient()

    session.request.return_value = _mock_response_with_exception(
        status=requests.codes.bad_request, json_data={}
    )
    with pytest.raises(ApiException) as execinfo:
        client.request(
            "GET",
            "https://example-10.com/test",
        )

    assert str(execinfo.value) == "Unknown error"
