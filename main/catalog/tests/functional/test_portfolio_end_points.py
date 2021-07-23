""" Test portfolio end points """
import json
import pytest
from django.urls import reverse
from main.tests.factories import TenantFactory
from main.catalog.tests.factories import PortfolioFactory
from main.catalog.tests.factories import PortfolioItemFactory


@pytest.mark.django_db
def test_portfolio_list(api_request):
    """Get List of Portfolios"""
    PortfolioFactory()
    response = api_request("get", reverse("portfolio-list"))

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1


@pytest.mark.django_db
def test_portfolio_retrieve(api_request):
    """Retrieve a single portfolio by id"""
    portfolio = PortfolioFactory()
    response = api_request(
        "get", reverse("portfolio-detail", args=(portfolio.id,))
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == portfolio.id


@pytest.mark.django_db
def test_portfolio_delete(api_request):
    """Delete a single portfolio by id"""
    portfolio = PortfolioFactory()
    response = api_request(
        "delete", reverse("portfolio-detail", args=(portfolio.id,))
    )

    assert response.status_code == 204


@pytest.mark.django_db
def test_portfolio_patch(api_request):
    """Patch a single portfolio by id"""
    portfolio = PortfolioFactory()
    data = {"name": "update"}
    response = api_request(
        "patch", reverse("portfolio-detail", args=(portfolio.id,)), data
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_portfolio_put_not_supported(api_request):
    """PUT is not supported"""
    portfolio = PortfolioFactory()
    data = {"name": "update"}
    response = api_request(
        "put", reverse("portfolio-detail", args=(portfolio.id,)), data
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_portfolio_post(api_request):
    """Create a Portfolio"""
    TenantFactory()
    data = {"name": "abcdef", "description": "abc"}
    response = api_request("post", reverse("portfolio-list"), data)

    assert response.status_code == 201

@pytest.mark.django_db
def test_portfolio_portfolio_items_get(api_request):
    """List PortfolioItems by portfolio id"""
    tenant = TenantFactory()
    portfolio1 = PortfolioFactory(tenant=tenant)
    portfolio2 = PortfolioFactory(tenant=tenant)
    PortfolioItemFactory(portfolio=portfolio1, tenant=tenant)
    PortfolioItemFactory(portfolio=portfolio1, tenant=tenant)
    portfolio_item3 = PortfolioItemFactory(portfolio=portfolio2, tenant=tenant)

    response = api_request(
        "get", reverse("portfolio-portfolioitem-list", args=(portfolio2.id,))
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1
    assert content["results"][0]["id"] == portfolio_item3.id
