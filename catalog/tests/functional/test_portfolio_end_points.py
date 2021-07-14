""" Test portfolio end points """
import json
import pytest
from django.urls import reverse
from catalog.tests.factories import PortfolioFactory
from catalog.tests.factories import PortfolioItemFactory
from catalog.tests.factories import TenantFactory


@pytest.mark.django_db
def test_portfolio_list(api_request):
    """Get List of Portfolios"""
    PortfolioFactory()
    response = api_request("get", reverse("catalog:portfolio-list"))

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1


@pytest.mark.django_db
def test_portfolio_retrieve(api_request):
    """Retrieve a single portfolio by id"""
    portfolio = PortfolioFactory()
    response = api_request(
        "get", reverse("catalog:portfolio-detail", args=(portfolio.id,))
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == portfolio.id


@pytest.mark.django_db
def test_portfolio_delete(api_request):
    """Delete a single portfolio by id"""
    portfolio = PortfolioFactory()
    response = api_request(
        "delete", reverse("catalog:portfolio-detail", args=(portfolio.id,))
    )

    assert response.status_code == 204


@pytest.mark.django_db
def test_portfolio_patch(api_request):
    """Patch a single portfolio by id"""
    portfolio = PortfolioFactory()
    data = {"name": "update"}
    response = api_request(
        "patch", reverse("catalog:portfolio-detail", args=(portfolio.id,)), data
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_portfolio_put_not_supported(api_request):
    """PUT is not supported"""
    portfolio = PortfolioFactory()
    data = {"name": "update"}
    response = api_request(
        "put", reverse("catalog:portfolio-detail", args=(portfolio.id,)), data
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_portfolio_post(api_request):
    """Create a Portfolio"""
    TenantFactory()
    data = {"name": "abcdef", "description": "abc"}
    response = api_request("post", reverse("catalog:portfolio-list"), data)

    assert response.status_code == 201


@pytest.mark.django_db
def test_portfolio_portfolio_items_get(api_request):
    """List PortfolioItems by portfolio id"""
    portfolio = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(portfolio=portfolio)
    response = api_request(
        "get", reverse("catalog:portfolio-portfolio_items", args=(portfolio.id,))
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1
    assert content["results"][0]["id"] == portfolio_item.id
