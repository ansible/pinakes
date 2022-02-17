""" Module to test PortfolioItem end points """
import os
import glob

import json
import pytest

from automation_services_catalog.main.catalog.models import PortfolioItem
from automation_services_catalog.main.catalog.services.copy_portfolio_item import (
    CopyPortfolioItem,
)
from automation_services_catalog.main.catalog.tests.factories import (
    PortfolioFactory,
)
from automation_services_catalog.main.catalog.tests.factories import (
    PortfolioItemFactory,
)

from automation_services_catalog.main.inventory.tests.factories import (
    ServiceOfferingFactory,
)


@pytest.mark.django_db
def test_portfolio_item_list(api_request):
    """Get list of Portfolio Items"""
    PortfolioItemFactory()
    response = api_request("get", "catalog:portfolioitem-list")

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1


@pytest.mark.django_db
def test_portfolio_item_retrieve(api_request):
    """Retrieve a single portfolio item by id"""
    portfolio_item = PortfolioItemFactory()
    response = api_request(
        "get", "catalog:portfolioitem-detail", portfolio_item.id
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == portfolio_item.id


@pytest.mark.django_db
def test_portfolio_item_delete(api_request):
    """Delete a PortfolioItem by id"""
    portfolio_item = PortfolioItemFactory()
    response = api_request(
        "delete", "catalog:portfolioitem-detail", portfolio_item.id
    )

    assert response.status_code == 204


@pytest.mark.django_db
def test_portfolio_item_patch(api_request):
    """PATCH a portfolio item by ID"""
    portfolio_item = PortfolioItemFactory()
    data = {"name": "update"}
    response = api_request(
        "patch",
        "catalog:portfolioitem-detail",
        portfolio_item.id,
        data,
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_portfolio_item_put(api_request):
    """PUT on portfolio item is not supported"""
    portfolio_item = PortfolioItemFactory()
    data = {"name": "update"}
    response = api_request(
        "put", "catalog:portfolioitem-detail", portfolio_item.id, data
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_portfolio_item_post(api_request):
    """Create a new portfolio item for a portfolio"""
    service_offering = ServiceOfferingFactory()
    portfolio = PortfolioFactory()
    data = {
        "portfolio": portfolio.id,
        "service_offering_ref": str(service_offering.id),
    }
    response = api_request("post", "catalog:portfolioitem-list", data=data)
    assert response.status_code == 201


@pytest.mark.django_db
def test_portfolio_item_post_with_exception(api_request):
    """Create a new portfolio item for a portfolio"""
    portfolio = PortfolioFactory()
    data = {
        "portfolio": portfolio.id,
    }

    response = api_request("post", "catalog:portfolioitem-list", data=data)

    assert response.status_code == 400
    assert "service_offering_ref" in response.data["errors"]


@pytest.mark.django_db
def test_portfolio_item_icon_post(api_request, small_image, media_dir):
    """Create a icon image for a portfolio item"""
    image_path = os.path.join(media_dir, "*.png")
    orignal_images = glob.glob(image_path)

    portfolio_item = PortfolioItemFactory()
    data = {"file": small_image, "source_ref": "abc"}

    assert portfolio_item.icon is None

    response = api_request(
        "post",
        "catalog:portfolioitem-icon",
        portfolio_item.id,
        data,
        format="multipart",
    )

    assert response.status_code == 200
    assert response.data["icon_url"]
    portfolio_item.refresh_from_db()
    assert portfolio_item.icon is not None

    images = glob.glob(image_path)
    assert len(images) == len(orignal_images) + 1

    portfolio_item.delete()


@pytest.mark.django_db
def test_portfolio_item_icon_patch(
    api_request, small_image, another_image, media_dir
):
    """Update a icon image for a portfolio item"""
    image_path = os.path.join(media_dir, "*.png")

    portfolio_item = PortfolioItemFactory()

    data = {"file": small_image, "source_ref": "abc"}

    response = api_request(
        "post",
        "catalog:portfolioitem-icon",
        portfolio_item.id,
        data,
        format="multipart",
    )
    original_url = response.data["icon_url"]
    orignal_images = glob.glob(image_path)

    data = {"file": another_image}

    response = api_request(
        "patch",
        "catalog:portfolioitem-icon",
        portfolio_item.id,
        data,
        format="multipart",
    )

    assert response.status_code == 200
    assert response.data["icon_url"] != original_url

    images = glob.glob(image_path)
    assert len(images) == len(orignal_images)
    portfolio_item.refresh_from_db()
    assert portfolio_item.icon is not None
    portfolio_item.delete()


@pytest.mark.django_db
def test_portfolio_item_icon_delete(api_request, small_image, media_dir):
    """Update a icon image for a portfolio item"""
    image_path = os.path.join(media_dir, "*.png")

    portfolio_item = PortfolioItemFactory()

    data = {"file": small_image, "source_ref": "abc"}

    api_request(
        "post",
        "catalog:portfolioitem-icon",
        portfolio_item.id,
        data,
        format="multipart",
    )
    orignal_images = glob.glob(image_path)

    response = api_request(
        "delete",
        "catalog:portfolioitem-icon",
        portfolio_item.id,
    )

    assert response.status_code == 204

    images = glob.glob(image_path)
    assert len(images) == len(orignal_images) - 1
    portfolio_item.refresh_from_db()
    assert portfolio_item.icon is None


@pytest.mark.django_db
def test_portfolio_item_copy(api_request, mocker):
    """Copy a PortfolioItem by id"""
    portfolio_item = PortfolioItemFactory()
    mocker.patch.object(CopyPortfolioItem, "_is_orderable", return_value=True)

    assert PortfolioItem.objects.count() == 1
    response = api_request(
        "post",
        "catalog:portfolioitem-copy",
        portfolio_item.id,
    )

    assert response.status_code == 200
    assert PortfolioItem.objects.count() == 2
    assert (
        PortfolioItem.objects.last().name == f"Copy of {portfolio_item.name}"
    )


@pytest.mark.django_db
def test_next_name_in_same_portfolio(api_request):
    portfolio = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(name="test", portfolio=portfolio)

    response = api_request(
        "get",
        "catalog:portfolioitem-next-name",
        portfolio_item.id,
    )

    assert response.status_code == 200
    assert response.data["next_name"] == f"Copy of {portfolio_item.name}"


@pytest.mark.django_db
def test_next_name_in_different_portfolio(api_request):
    portfolio_1 = PortfolioFactory()
    PortfolioItemFactory(name="test", portfolio=portfolio_1)
    PortfolioItemFactory(name="Copy of test", portfolio=portfolio_1)

    portfolio_2 = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(name="test", portfolio=portfolio_2)

    data = {"destination_portfolio_id": portfolio_1.id}

    response = api_request(
        "get",
        "catalog:portfolioitem-next-name",
        portfolio_item.id,
        data,
    )

    assert response.status_code == 200
    assert response.data["next_name"] == f"Copy (1) of {portfolio_item.name}"
