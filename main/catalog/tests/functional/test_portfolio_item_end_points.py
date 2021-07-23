""" Module to test PortfolioItem end points """
import json
import pytest
from django.urls import reverse
from main.catalog.tests.factories import PortfolioFactory
from main.catalog.tests.factories import PortfolioItemFactory


@pytest.mark.django_db
def test_portfolio_item_list(api_request):
    """Get list of Portfolio Items"""
    PortfolioItemFactory()
    response = api_request("get", reverse("portfolioitem-list"))

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1


@pytest.mark.django_db
def test_portfolio_item_retrieve(api_request):
    """Retrieve a single portfolio item by id"""
    portfolio_item = PortfolioItemFactory()
    response = api_request(
        "get", reverse("portfolioitem-detail", args=(portfolio_item.id,))
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == portfolio_item.id


@pytest.mark.django_db
def test_portfolio_item_delete(api_request):
    """Delete a PortfolioItem by id"""
    portfolio_item = PortfolioItemFactory()
    response = api_request(
        "delete", reverse("portfolioitem-detail", args=(portfolio_item.id,))
    )

    assert response.status_code == 204


@pytest.mark.django_db
def test_portfolio_item_patch(api_request):
    """PATCH a portfolio item by ID"""
    portfolio_item = PortfolioItemFactory()
    data = {"name": "update"}
    response = api_request(
        "patch",
        reverse("portfolioitem-detail", args=(portfolio_item.id,)),
        data,
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_portfolio_item_put(api_request):
    """PUT on portfolio item is not supported"""
    portfolio_item = PortfolioItemFactory()
    data = {"name": "update"}
    response = api_request(
        "put", reverse("portfolioitem-detail", args=(portfolio_item.id,)), data
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_portfolio_item_post(api_request):
    """Create a new portfolio item for a portfolio"""
    portfolio = PortfolioFactory()
    data = {
        "portfolio": portfolio.id,
        "service_offering_ref": "1234",
        "name": "abcdef",
        "description": "abc",
    }
    response = api_request("post", reverse("portfolioitem-list"), data)
    assert response.status_code == 201
