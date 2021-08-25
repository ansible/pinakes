""" Test service_plan end points """
import json
import pytest

from django.urls import reverse
from main.catalog.tests.factories import (
    PortfolioItemFactory,
    ServicePlanFactory,
)


@pytest.mark.django_db
def test_portfolio_item_service_plan_get(api_request):
    """List CatalogServicePlan by PortfolioItem id"""
    portfolio_item = PortfolioItemFactory()

    ServicePlanFactory(portfolio_item=portfolio_item)

    response = api_request(
        "get",
        reverse("portfolioitem-serviceplan-list", args=(portfolio_item.id,)),
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1
    assert content["results"][0]["id"] == portfolio_item.id
