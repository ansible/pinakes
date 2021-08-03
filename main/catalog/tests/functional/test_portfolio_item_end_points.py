""" Module to test PortfolioItem end points """
import os
import glob

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


@pytest.mark.django_db
def test_portfolio_item_icon_post(api_request, small_image, media_dir):
    """Create a icon image for a portfolio item"""
    image_path = os.path.join(media_dir, "*.png")
    orignal_images = glob.glob(image_path)

    portfolio_item = PortfolioItemFactory()
    data = {"icon": small_image, "source_ref": "abc"}

    assert portfolio_item.icon is None

    response = api_request(
        "post",
        reverse("portfolioitem-icon", args=(portfolio_item.id,)),
        data,
        format="multipart",
    )

    assert response.status_code == 201
    portfolio_item.refresh_from_db()
    assert portfolio_item.icon is not None

    images = glob.glob(image_path)
    assert len(images) == len(orignal_images) + 1


@pytest.mark.django_db
def test_portfolio_item_icon_patch(api_request, small_image, media_dir):
    """Update a icon image for a portfolio item"""
    image_path = os.path.join(media_dir, "*.png")

    portfolio_item = PortfolioItemFactory()

    data = {"icon": small_image, "source_ref": "abc"}

    api_request(
        "post",
        reverse("portfolioitem-icon", args=(portfolio_item.id,)),
        data,
        format="multipart",
    )
    orignal_images = glob.glob(image_path)

    response = api_request(
        "patch",
        reverse("portfolioitem-icon", args=(portfolio_item.id,)),
        data,
        format="multipart",
    )

    assert response.status_code == 201

    images = glob.glob(image_path)
    assert len(images) == len(orignal_images)
    portfolio_item.refresh_from_db()
    assert portfolio_item.icon is not None


@pytest.mark.django_db
def test_portfolio_item_icon_delete(api_request, small_image, media_dir):
    """Update a icon image for a portfolio item"""
    image_path = os.path.join(media_dir, "*.png")
    orignal_images = glob.glob(image_path)

    portfolio_item = PortfolioItemFactory()

    data = {"icon": small_image, "source_ref": "abc"}

    api_request(
        "post",
        reverse("portfolioitem-icon", args=(portfolio_item.id,)),
        data,
        format="multipart",
    )

    response = api_request(
        "delete",
        reverse("portfolioitem-icon", args=(portfolio_item.id,)),
        data,
        format="multipart",
    )

    assert response.status_code == 204

    images = glob.glob(image_path)
    assert len(images) == len(orignal_images)
    portfolio_item.refresh_from_db()
    assert portfolio_item.icon is None
