""" Test for tagging  """
import json
import pytest

from django.urls import reverse
from main.catalog.tests.factories import PortfolioFactory


@pytest.mark.django_db
def test_portfolio_tag_add(api_request):
    """Test adding a tag on portfolio"""
    portfolio = PortfolioFactory()
    url = reverse("portfolio-tag", args=(portfolio.id,))
    response = api_request("post", url, {"name": "test_tag"})

    assert response.status_code == 201
    content = json.loads(response.content)

    assert content["name"] == "test_tag"


@pytest.mark.django_db
def test_portfolio_tags_list(api_request):
    """Test tag list for a portfolio"""
    portfolio = PortfolioFactory()

    # Add tag first
    url = reverse("portfolio-tag", args=(portfolio.id,))
    api_request("post", url, {"name": "test_tag"})

    # List tags
    url = reverse("portfolio-tags", args=(portfolio.id,))
    response = api_request("get", url)

    assert response.status_code == 200
    content = json.loads(response.content)

    assert len(content) == 1
    assert content[0]["name"] == "test_tag"


@pytest.mark.django_db
def test_portfolio_tags_remove(api_request):
    """Test Removal of Tag"""
    portfolio = PortfolioFactory()

    # Add tag first
    url = reverse("portfolio-tag", args=(portfolio.id,))
    api_request("post", url, {"name": "test_tag"})

    # Remove tag
    url = reverse("portfolio-untag", args=(portfolio.id,))
    response = api_request("post", url, {"name": "test_tag"})

    assert response.status_code == 204
