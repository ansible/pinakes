""" Test for tagging  """
import json
import pytest

from django.urls import reverse
from catalog.tests.factories import PortfolioFactory


@pytest.mark.django_db
class TestPortfolioTagsEndPoints:
    """ Test for tagging on portfolio """

    def test_portfolio_tag_add(self, api_client):
        portfolio = PortfolioFactory()
        url = reverse("catalog:portfolio-tag", args=(portfolio.id,))
        response = api_client.post(url, {"name": "test_tag"}, format="json")

        assert response.status_code == 201
        content = json.loads(response.content)

        assert content["name"] == "test_tag"

    def test_portfolio_tags_list(self, api_client):
        portfolio = PortfolioFactory()

        # Add tag first
        url = reverse("catalog:portfolio-tag", args=(portfolio.id,))
        api_client.post(url, {"name": "test_tag"}, format="json")

        # List tags
        url = reverse("catalog:portfolio-tags", args=(portfolio.id,))
        response = api_client.get(url)

        assert response.status_code == 200
        content = json.loads(response.content)

        assert len(content) == 1
        assert content[0]["name"] == "test_tag"

    def test_portfolio_tags_remove(self, api_client):
        portfolio = PortfolioFactory()

        # Add tag first
        url = reverse("catalog:portfolio-tag", args=(portfolio.id,))
        api_client.post(url, {"name": "test_tag"}, format="json")

        # Remove tag
        url = reverse("catalog:portfolio-untag", args=(portfolio.id,))
        response = api_client.post(url, {"name": "test_tag"}, format="json")

        assert response.status_code == 204
