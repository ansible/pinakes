""" Module to test session logout end point """
import json
import pytest


@pytest.mark.django_db
def test_session_logout(api_request, mocker):
    """Logout an authenticated user from a single session"""
    mocker.patch("ansible_catalog.main.auth.views.OpenIdConnect")
    response = api_request("post", "logout")
    assert response.status_code == 200
