"""Module to test CurrentUser end points"""
import json

import pytest

from django.contrib.auth import get_user_model


User = get_user_model()


@pytest.mark.django_db
def test_current_me_authenticated(api_request):
    """Retrieve currently logged in user"""
    fred = User(
        username="fred",
        is_superuser=False,
        password="normal",
        first_name="Fred",
        last_name="Sample",
    )
    fred.save()
    response = api_request("get", "auth:me", None, None, fred)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["username"] == "fred"
    assert content["last_name"] == "Sample"
    assert content["first_name"] == "Fred"
    assert sorted(content["roles"]) == ["approval-admin", "catalog-admin"]


@pytest.mark.django_db
def test_current_me_unauthenticated(api_request):
    """Unauthenticated user should return 403"""
    fred = User(
        username="fred",
        is_superuser=False,
        password="normal",
        first_name="Fred",
        last_name="Sample",
    )
    fred.save()
    response = api_request("get", "auth:me", None, None, fred, "json", False)

    assert response.status_code == 403
