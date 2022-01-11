""" Test portfolio end points """
import json
import os
import glob

from unittest.mock import patch
from unittest import mock
import pytest

from ansible_catalog.main.models import Image
from ansible_catalog.main.catalog.models import (
    Portfolio,
    PortfolioItem,
)
from ansible_catalog.main.catalog.tests.factories import (
    ImageFactory,
    PortfolioFactory,
    PortfolioItemFactory,
)

from ansible_catalog.main.auth.tests.factories import GroupFactory
from ansible_catalog.common.auth.keycloak.models import UmaPermission
from ansible_catalog.common.auth.keycloak_django.utils import (
    make_permission_name,
    make_scope,
)


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
def test_portfolio_copy(api_request):
    """Copy a portfolio by id"""
    portfolio = PortfolioFactory()
    data = {"portfolio_name": "new_copied_name"}

    response = api_request("post", "portfolio-copy", portfolio.id, data)

    assert response.status_code == 200
    assert Portfolio.objects.count() == 2
    assert Portfolio.objects.last().name == "new_copied_name"


@pytest.mark.django_db
def test_portfolio_copy_with_portfolio_items(api_request):
    """Copy a portfolio by id"""
    portfolio = PortfolioFactory()
    PortfolioItemFactory(portfolio=portfolio)
    item = PortfolioItemFactory(portfolio=portfolio)

    assert Portfolio.objects.count() == 1
    assert PortfolioItem.objects.count() == 2

    with patch(
        "ansible_catalog.main.catalog.services.copy_portfolio_item.CopyPortfolioItem._is_orderable"
    ) as mock:
        mock.return_value = True

        response = api_request("post", "portfolio-copy", portfolio.id, {})

    assert response.status_code == 200
    assert Portfolio.objects.count() == 2
    assert Portfolio.objects.last().name == "Copy of %s" % portfolio.name
    assert PortfolioItem.objects.count() == 4
    assert PortfolioItem.objects.filter(portfolio=portfolio).count() == 2
    assert PortfolioItem.objects.last().name == item.name


@pytest.mark.django_db
def test_portfolio_copy_with_icon(api_request):
    """Copy a portfolio by id"""
    image = ImageFactory()
    portfolio = PortfolioFactory(icon=image)

    assert Portfolio.objects.count() == 1
    assert Image.objects.count() == 1

    response = api_request("post", "portfolio-copy", portfolio.id, {})

    assert response.status_code == 200
    assert Portfolio.objects.count() == 2
    assert Image.objects.count() == 2

    Portfolio.objects.last().delete()


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


@pytest.mark.django_db
def test_portfolio_share_info(api_request, mocker):
    """Test Share Information of Portfolio"""
    group = GroupFactory()
    portfolio = PortfolioFactory()
    action = Portfolio.KEYCLOAK_ACTIONS[0]

    client_mock = mock.Mock()
    mocker.patch(
        "ansible_catalog.common.auth.keycloak_django.get_uma_client",
        return_value=client_mock,
    )
    permission = UmaPermission(
        name=make_permission_name(portfolio, group),
        groups=[group.path],
        scopes=[make_scope(portfolio, action)],
    )
    client_mock.find_permissions_by_resource.return_value = [permission]

    response = api_request("get", "portfolio-share-info", portfolio.id)

    assert response.status_code == 200
    shares = json.loads(response.content)
    assert (len(shares)) == 1
    assert shares[0]["group_id"] == group.id
    assert shares[0]["group_name"] == group.name
    assert shares[0]["permissions"][0] == action
