import pytest
from django.test import TestCase

TestCase.databases = {"default", "approval"}

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()
