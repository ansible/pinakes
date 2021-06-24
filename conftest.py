import pytest
from django.contrib.auth.models import User


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    client = APIClient()
    test_user = User.objects.create(username="flintstone")
    client.force_login(test_user)
    return client
