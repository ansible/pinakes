""" Module to test logout end point """
import json
import pytest
from requests import Session


@pytest.mark.django_db
def test_logout(api_request, mocker):
    """Logout an authenticated user"""
    mocker.patch(
        "ansible_catalog.common.auth.keycloak_django.clients.get_admin_client"
    )
    response = api_request("post", "logout")
    assert response.status_code == 200
