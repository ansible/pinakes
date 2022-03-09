"""Test about view"""
import pytest


@pytest.mark.django_db
def test_about(api_request):
    """Test about GET endpoint"""
    response = api_request("get", "common:about")
    assert response.status_code == 200
    assert "product_name" in response.data
    assert "version" in response.data
