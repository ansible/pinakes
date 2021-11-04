""" Test portfolio end points """
import json
import pytest

import os
import glob

from ansible_catalog.main.catalog.tests.factories import PortfolioFactory
from ansible_catalog.main.catalog.tests.factories import PortfolioItemFactory


@pytest.mark.django_db
def test_portfolio_list(api_request):
    """Get List of Portfolios"""
    PortfolioFactory()
    response = api_request("get", "portfolio-list")

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1


@pytest.mark.django_db
def test_portfolio_retrieve(api_request):
    """Retrieve a single portfolio by id"""
    portfolio = PortfolioFactory()
    response = api_request("get", "portfolio-detail", portfolio.id)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == portfolio.id


@pytest.mark.django_db
def test_portfolio_delete(api_request):
    """Delete a single portfolio by id"""
    portfolio = PortfolioFactory()
    response = api_request("delete", "portfolio-detail", portfolio.id)

    assert response.status_code == 204


@pytest.mark.django_db
def test_portfolio_patch(api_request):
    """Patch a single portfolio by id"""
    portfolio = PortfolioFactory()
    data = {"name": "update"}
    response = api_request("patch", "portfolio-detail", portfolio.id, data)

    assert response.status_code == 200


@pytest.mark.django_db
def test_portfolio_put_not_supported(api_request):
    """PUT is not supported"""
    portfolio = PortfolioFactory()
    data = {"name": "update"}
    response = api_request("put", "portfolio-detail", portfolio.id, data)

    assert response.status_code == 405


@pytest.mark.django_db
def test_portfolio_post(api_request):
    """Create a Portfolio"""
    data = {"name": "abcdef", "description": "abc"}
    response = api_request("post", "portfolio-list", data=data)

    assert response.status_code == 201


@pytest.mark.django_db
def test_portfolio_portfolio_items_get(api_request):
    """List PortfolioItems by portfolio id"""
    portfolio1 = PortfolioFactory()
    portfolio2 = PortfolioFactory()
    PortfolioItemFactory(portfolio=portfolio1)
    PortfolioItemFactory(portfolio=portfolio1)
    portfolio_item3 = PortfolioItemFactory(portfolio=portfolio2)

    response = api_request(
        "get", "portfolio-portfolioitem-list", portfolio2.id
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1
    assert content["results"][0]["id"] == portfolio_item3.id


@pytest.mark.django_db
def test_portfolio_portfolio_items_get_bad_id(api_request):
    """List PortfolioItems by non-existing id"""
    response = api_request("get", "portfolio-portfolioitem-list", -1)

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 0


@pytest.mark.django_db
def test_portfolio_portfolio_items_get_string_id(api_request):
    """List PortfolioItems by fake string id"""
    response = api_request("get", "portfolio-portfolioitem-list", "abc")

    assert response.status_code == 404


@pytest.mark.django_db
def test_portfolio_icon_post(api_request, small_image, media_dir):
    """Create a icon image for a portfolio"""
    image_path = os.path.join(media_dir, "*.png")
    orignal_images = glob.glob(image_path)

    portfolio = PortfolioFactory()
    data = {"file": small_image, "source_ref": "abc"}

    assert portfolio.icon is None

    response = api_request(
        "post",
        "portfolio-icon",
        portfolio.id,
        data,
        format="multipart",
    )

    assert response.status_code == 200
    assert response.data["icon_url"]

    portfolio.refresh_from_db()
    assert portfolio.icon is not None

    images = glob.glob(image_path)
    assert len(images) == len(orignal_images) + 1

    portfolio.delete()


@pytest.mark.django_db
def test_portfolio_icon_patch(
    api_request, small_image, another_image, media_dir
):
    """Update a icon image for a portfolio"""
    image_path = os.path.join(media_dir, "*.png")

    portfolio = PortfolioFactory()

    data = {"file": small_image, "source_ref": "abc"}

    response = api_request(
        "post",
        "portfolio-icon",
        portfolio.id,
        data,
        format="multipart",
    )
    original_url = response.data["icon_url"]
    orignal_images = glob.glob(image_path)

    data = {"file": another_image}

    response = api_request(
        "patch",
        "portfolio-icon",
        portfolio.id,
        data,
        format="multipart",
    )

    assert response.status_code == 200
    assert response.data["icon_url"] != original_url

    images = glob.glob(image_path)
    assert len(images) == len(orignal_images)
    portfolio.refresh_from_db()
    assert portfolio.icon is not None
    portfolio.delete()


@pytest.mark.django_db
def test_portfolio_icon_delete(api_request, small_image, media_dir):
    """Update a icon image for a portfolio"""
    image_path = os.path.join(media_dir, "*.png")

    portfolio = PortfolioFactory()

    data = {"file": small_image, "source_ref": "abc"}

    api_request(
        "post",
        "portfolio-icon",
        portfolio.id,
        data,
        format="multipart",
    )
    orignal_images = glob.glob(image_path)

    response = api_request(
        "delete",
        "portfolio-icon",
        portfolio.id,
    )

    assert response.status_code == 204

    images = glob.glob(image_path)
    assert len(images) == len(orignal_images) - 1
    portfolio.refresh_from_db()
    assert portfolio.icon is None
