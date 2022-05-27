"""Test for tagging"""
import json
import pytest

from pinakes.main.catalog.tests.factories import (
    PortfolioFactory,
)


@pytest.mark.django_db
def test_portfolio_tag_add(api_request):
    """Test adding a tag on portfolio"""
    portfolio = PortfolioFactory()
    response = api_request(
        "post", "catalog:portfolio-tag", portfolio.id, {"name": "test_tag"}
    )

    assert response.status_code == 201
    content = json.loads(response.content)

    assert content["name"] == "test_tag"


@pytest.mark.django_db
def test_portfolio_tags_list(api_request):
    """Test tag list for a portfolio"""
    portfolio = PortfolioFactory()

    # Add tag first
    api_request(
        "post", "catalog:portfolio-tag", portfolio.id, {"name": "test_tag"}
    )

    # List tags
    response = api_request("get", "catalog:portfolio-tags", portfolio.id)

    assert response.status_code == 200
    content = json.loads(response.content)

    assert len(content["results"]) == 1
    assert content["results"][0]["name"] == "test_tag"


@pytest.mark.django_db
def test_portfolio_tags_remove(api_request):
    """Test Removal of Tag"""
    portfolio = PortfolioFactory()

    # Add tag first
    api_request(
        "post", "catalog:portfolio-tag", portfolio.id, {"name": "test_tag"}
    )

    # Remove tag
    response = api_request(
        "post", "catalog:portfolio-untag", portfolio.id, {"name": "test_tag"}
    )

    assert response.status_code == 204
