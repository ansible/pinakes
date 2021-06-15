import pytest
import json
from django.urls import reverse
from catalog.tests.factories import PortfolioFactory
from catalog.tests.factories import PortfolioItemFactory
from catalog.tests.factories import TenantFactory


@pytest.mark.django_db
class TestPortfolioEndPoints:
    def test_portfolio_list(self, api_client):
        PortfolioFactory()
        url = reverse("catalog:portfolio-list")
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)

        assert content["count"] == 1

    def test_portfolio_retrieve(self, api_client):
        portfolio = PortfolioFactory()
        url = reverse("catalog:portfolio-detail", args=(portfolio.id,))
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)
        assert content["id"] == portfolio.id

    def test_portfolio_delete(self, api_client):
        portfolio = PortfolioFactory()
        url = reverse("catalog:portfolio-detail", args=(portfolio.id,))
        response = api_client.delete(url)

        assert response.status_code == 204

    def test_portfolio_patch(self, api_client):
        portfolio = PortfolioFactory()
        url = reverse("catalog:portfolio-detail", args=(portfolio.id,))
        response = api_client.patch(url, {"name": "update"}, format="json")

        assert response.status_code == 200

    def test_portfolio_put_not_supported(self, api_client):
        portfolio = PortfolioFactory()
        url = reverse("catalog:portfolio-detail", args=(portfolio.id,))
        response = api_client.put(url, {"name": "update"}, format="json")

        assert response.status_code == 405

    def test_portfolio_post(self, api_client):
        TenantFactory()
        url = reverse("catalog:portfolio-list")
        response = api_client.post(
            url, {"name": "abcdef", "description": "abc"}, format="json"
        )

        assert response.status_code == 201

    def test_portfolio_portfolio_items_get(self, api_client):
        portfolio = PortfolioFactory()
        portfolio_item = PortfolioItemFactory(portfolio=portfolio)
        url = reverse("catalog:portfolio-portfolio_items", args=(portfolio.id,))
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)

        assert content["count"] == 1
        assert content["results"][0]["id"] == portfolio_item.id
