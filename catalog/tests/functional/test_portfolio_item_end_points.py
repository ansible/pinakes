import pytest
import json
from django.urls import reverse
from catalog.tests.factories import PortfolioFactory
from catalog.tests.factories import PortfolioItemFactory


@pytest.mark.django_db
class TestPortfolioItemEndPoints:
    def test_portfolio_item_list(self, api_client):
        PortfolioItemFactory()
        url = reverse("portfolioitem-list")
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)

        assert content["count"] == 1

    def test_portfolio_item_retrieve(self, api_client):
        portfolio_item = PortfolioItemFactory()
        url = reverse("portfolioitem-detail", args=(portfolio_item.id,))
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)
        assert content["id"] == portfolio_item.id

    def test_portfolio_item_delete(self, api_client):
        portfolio_item = PortfolioItemFactory()
        url = reverse("portfolioitem-detail", args=(portfolio_item.id,))
        response = api_client.delete(url)

        assert response.status_code == 204

    def test_portfolio_item_patch(self, api_client):
        portfolio_item = PortfolioItemFactory()
        url = reverse("portfolioitem-detail", args=(portfolio_item.id,))
        response = api_client.patch(url, {"name": "update"}, format="json")

        assert response.status_code == 200

    def test_portfolio_item_put_not_supported(self, api_client):
        portfolio_item = PortfolioItemFactory()
        url = reverse("portfolioitem-detail", args=(portfolio_item.id,))
        response = api_client.put(url, {"name": "update"}, format="json")

        assert response.status_code == 405

    def test_portfolio_item_post(self, api_client):
        portfolio = PortfolioFactory()
        url = reverse("portfolioitem-list")
        response = api_client.post(
            url,
            {
                "portfolio": portfolio.id,
                "service_offering_ref": "1234",
                "name": "abcdef",
                "description": "abc",
            },
            format="json",
        )

        assert response.status_code == 201
