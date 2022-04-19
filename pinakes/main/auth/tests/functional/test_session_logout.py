"""Module to test session logout end point."""
import pytest
from rest_framework import status


@pytest.mark.django_db
def test_session_logout(api_request, mocker):
    """Logout an authenticated user from a single session"""
    mocker.patch("pinakes.main.auth.views.get_oidc_client")
    response = api_request("post", "auth:logout")
    assert response.status_code == status.HTTP_204_NO_CONTENT
