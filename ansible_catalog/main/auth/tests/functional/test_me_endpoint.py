""" Module to test CurrentUser end points """
import json
import pytest
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_current_me_authenticated(api_request):
    """Retrieve currently logged in user"""
    fred = User(
        username="fred",
        is_superuser=False,
        password="normal",
        first_name="Fred",
        last_name="Flintstone",
    )
    fred.save()
    response = api_request("get", "me", None, None, fred)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["username"] == "fred"
    assert content["last_name"] == "Flintstone"
    assert content["first_name"] == "Fred"


@pytest.mark.django_db
def test_current_me_unauthenticated(api_request):
    """Unauthenticated user should return 401"""
    fred = User(
        username="fred",
        is_superuser=False,
        password="normal",
        first_name="Fred",
        last_name="Flintstone",
    )
    fred.save()
    response = api_request("get", "me", None, None, fred, "json", False)

    assert response.status_code == 401
