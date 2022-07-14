"""Test portfolio end points"""
import json
import os
import glob

from unittest.mock import patch
from unittest import mock
import pytest

from pinakes.main.catalog.permissions import (
    PortfolioPermission,
)
from pinakes.main.models import Image
from pinakes.main.catalog.models import (
    Portfolio,
    PortfolioItem,
)
from pinakes.main.catalog.tests.factories import (
    ImageFactory,
    PortfolioFactory,
    PortfolioItemFactory,
)

from pinakes.main.common.tests.factories import (
    GroupFactory,
)
from pinakes.common.auth.keycloak.models import (
    UmaPermission,
)
from pinakes.common.auth.keycloak_django.utils import (
    make_permission_name,
    make_scope,
)


EXPECTED_USER_CAPABILITIES = {
    "retrieve": True,
    "update": True,
    "partial_update": True,
    "destroy": True,
    "tags": True,
    "tag": True,
    "untag": True,
    "share": True,
    "unshare": True,
    "share_info": True,
    "icon": True,
    "copy": True,
}


@pytest.mark.django_db
def test_portfolio_list(api_request, mocker):
    """Get List of Portfolios"""
    scope_queryset = mocker.spy(PortfolioPermission, "scope_queryset")

    PortfolioFactory()
    response = api_request("get", "catalog:portfolio-list")

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["count"] == 1

    results = content["results"]
    assert (
        results[0]["metadata"]["user_capabilities"]
        == EXPECTED_USER_CAPABILITIES
    )

    scope_queryset.assert_called_once()


@pytest.mark.django_db
def test_portfolio_retrieve(api_request):
    """Retrieve a single portfolio by id"""
    portfolio = PortfolioFactory()
    response = api_request("get", "catalog:portfolio-detail", portfolio.id)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == portfolio.id
    assert (
        content["metadata"]["user_capabilities"] == EXPECTED_USER_CAPABILITIES
    )


@pytest.mark.django_db
def test_portfolio_delete(api_request):
    """Delete a single portfolio by id"""
    portfolio = PortfolioFactory()
    response = api_request("delete", "catalog:portfolio-detail", portfolio.id)

    assert response.status_code == 204


@pytest.mark.django_db
def test_portfolio_patch(api_request):
    """Patch a single portfolio by id"""
    portfolio = PortfolioFactory()
    data = {"name": "update"}
    response = api_request(
        "patch", "catalog:portfolio-detail", portfolio.id, data
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_portfolio_copy(api_request, mocker):
    """Copy a portfolio by id"""
    has_object_permission = mocker.spy(
        PortfolioPermission, "has_object_permission"
    )
    portfolio = PortfolioFactory()
    data = {"portfolio_name": "new_copied_name"}

    response = api_request(
        "post", "catalog:portfolio-copy", portfolio.id, data
    )

    assert response.status_code == 200
    assert Portfolio.objects.count() == 2
    assert Portfolio.objects.last().name == "new_copied_name"

    has_object_permission.assert_called_once()
    assert has_object_permission.call_args.args[3].id == portfolio.id


@pytest.mark.django_db
def test_portfolio_copy_with_portfolio_items(api_request):
    """Copy a portfolio by id"""
    portfolio = PortfolioFactory()
    PortfolioItemFactory(portfolio=portfolio)
    item = PortfolioItemFactory(portfolio=portfolio)

    assert Portfolio.objects.count() == 1
    assert PortfolioItem.objects.count() == 2

    with patch(
        "pinakes.main.catalog.services.copy_portfolio_item."
        "CopyPortfolioItem._is_orderable"
    ) as mocked:
        mocked.return_value = True

        response = api_request(
            "post", "catalog:portfolio-copy", portfolio.id, {}
        )

    assert response.status_code == 200
    assert Portfolio.objects.count() == 2
    assert Portfolio.objects.last().name == f"Copy of {portfolio.name}"
    assert PortfolioItem.objects.count() == 4
    assert PortfolioItem.objects.filter(portfolio=portfolio).count() == 2
    assert PortfolioItem.objects.last().name == item.name


@pytest.mark.django_db
def test_portfolio_copy_with_icon(api_request):
    """Copy a portfolio by id"""
    image = ImageFactory()
    portfolio = PortfolioFactory(icon=image)

    assert Portfolio.objects.count() == 1
    old_count = Image.objects.count()

    response = api_request("post", "catalog:portfolio-copy", portfolio.id, {})

    assert response.status_code == 200
    assert Portfolio.objects.count() == 2
    assert Image.objects.count() == old_count + 1

    Portfolio.objects.last().delete()


@pytest.mark.django_db
def test_portfolio_put_not_supported(api_request):
    """PUT is not supported"""
    portfolio = PortfolioFactory()
    data = {"name": "update"}
    response = api_request(
        "put", "catalog:portfolio-detail", portfolio.id, data
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_portfolio_post(api_request):
    """Create a Portfolio"""
    data = {"name": "abcdef", "description": "abc"}
    response = api_request("post", "catalog:portfolio-list", data=data)

    assert response.status_code == 201

    response = api_request("post", "catalog:portfolio-list", data=data)
    # uniqueness
    assert response.status_code == 400


@pytest.mark.django_db
def test_portfolio_portfolio_items_get(api_request):
    """List PortfolioItems by portfolio id"""
    portfolio1 = PortfolioFactory()
    portfolio2 = PortfolioFactory()
    PortfolioItemFactory(portfolio=portfolio1)
    PortfolioItemFactory(portfolio=portfolio1)
    portfolio_item3 = PortfolioItemFactory(portfolio=portfolio2)

    response = api_request(
        "get", "catalog:portfolio-portfolioitem-list", portfolio2.id
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1
    assert content["results"][0]["id"] == portfolio_item3.id


@pytest.mark.django_db
def test_portfolio_portfolio_items_get_bad_id(api_request):
    """List PortfolioItems by non-existing id"""
    response = api_request("get", "catalog:portfolio-portfolioitem-list", -1)

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 0


@pytest.mark.django_db
def test_portfolio_portfolio_items_get_string_id(api_request):
    """List PortfolioItems by fake string id"""
    response = api_request(
        "get", "catalog:portfolio-portfolioitem-list", "abc"
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_portfolio_icon_post(api_request, mocker, small_image, media_dir):
    """Create a icon image for a portfolio"""
    has_object_permission = mocker.spy(
        PortfolioPermission, "has_object_permission"
    )
    image_path = os.path.join(media_dir, "*.png")
    orignal_images = glob.glob(image_path)

    portfolio = PortfolioFactory()
    data = {"file": small_image, "source_ref": "abc"}

    assert portfolio.icon is None

    response = api_request(
        "post",
        "catalog:portfolio-icon",
        portfolio.id,
        data,
        format="multipart",
    )

    assert response.status_code == 200
    assert response.data["icon_url"]

    has_object_permission.assert_called_once()
    assert has_object_permission.call_args.args[3].id == portfolio.id

    portfolio.refresh_from_db()
    assert portfolio.icon is not None

    images = glob.glob(image_path)
    assert len(images) == len(orignal_images) + 1

    portfolio.delete()


@pytest.mark.django_db
def test_portfolio_icon_patch(
    api_request, mocker, small_image, another_image, media_dir
):
    """Update a icon image for a portfolio"""
    image_path = os.path.join(media_dir, "*.png")

    portfolio = PortfolioFactory()

    data = {"file": small_image, "source_ref": "abc"}

    response = api_request(
        "post",
        "catalog:portfolio-icon",
        portfolio.id,
        data,
        format="multipart",
    )
    original_url = response.data["icon_url"]
    orignal_images = glob.glob(image_path)

    data = {"file": another_image}

    has_object_permission = mocker.spy(
        PortfolioPermission, "has_object_permission"
    )

    response = api_request(
        "patch",
        "catalog:portfolio-icon",
        portfolio.id,
        data,
        format="multipart",
    )

    assert response.status_code == 200
    assert response.data["icon_url"] != original_url

    has_object_permission.assert_called_once()
    assert has_object_permission.call_args.args[3].id == portfolio.id

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
        "catalog:portfolio-icon",
        portfolio.id,
        data,
        format="multipart",
    )
    orignal_images = glob.glob(image_path)

    response = api_request(
        "delete",
        "catalog:portfolio-icon",
        portfolio.id,
    )

    assert response.status_code == 204

    images = glob.glob(image_path)
    assert len(images) == len(orignal_images) - 1
    portfolio.refresh_from_db()
    assert portfolio.icon is None


@pytest.mark.django_db
def test_portfolio_share_info(api_request, mocker):
    """Test Share Information of Portfolio with keycloak_id set"""
    group = GroupFactory()
    portfolio = PortfolioFactory(keycloak_id="abc")

    client_mock = mock.Mock()
    mocker.patch(
        "pinakes.common.auth.keycloak_django.get_uma_client",
        return_value=client_mock,
    )
    has_object_permission = mocker.spy(
        PortfolioPermission, "has_object_permission"
    )
    permission = UmaPermission(
        name=make_permission_name(portfolio, group),
        groups=[group.path],
        scopes=[
            make_scope(portfolio, Portfolio.KEYCLOAK_ACTIONS[0]),
            make_scope(portfolio, Portfolio.KEYCLOAK_ACTIONS[1]),
        ],
    )
    client_mock.find_permissions_by_resource.return_value = [permission]

    response = api_request("get", "catalog:portfolio-share-info", portfolio.id)

    assert response.status_code == 200
    shares = json.loads(response.content)
    assert (len(shares)) == 1
    assert shares[0]["group_id"] == group.id
    assert shares[0]["group_name"] == group.name
    assert (
        shares[0]["permissions"].sort()
        == [
            Portfolio.KEYCLOAK_ACTIONS[0],
            Portfolio.KEYCLOAK_ACTIONS[1],
        ].sort()
    )

    has_object_permission.assert_called_once()
    assert has_object_permission.call_args.args[3].id == portfolio.id


@pytest.mark.django_db
def test_portfolio_share_info_empty(api_request):
    """Test Share Information of Portfolio without keycloak_id"""
    portfolio = PortfolioFactory()

    response = api_request("get", "catalog:portfolio-share-info", portfolio.id)

    assert response.status_code == 200
    shares = json.loads(response.content)
    assert len(shares) == 0


@pytest.mark.django_db
def test_portfolio_share_info_consolidated(api_request, mocker):
    """Test Share Information of Portfolio with separate permission set"""
    group = GroupFactory()
    portfolio = PortfolioFactory(keycloak_id="abc")

    client_mock = mock.Mock()
    mocker.patch(
        "pinakes.common.auth.keycloak_django.get_uma_client",
        return_value=client_mock,
    )
    has_object_permission = mocker.spy(
        PortfolioPermission, "has_object_permission"
    )
    permission1 = UmaPermission(
        name=make_permission_name(portfolio, group),
        groups=[group.path],
        scopes=[
            make_scope(portfolio, Portfolio.KEYCLOAK_ACTIONS[1]),
        ],
    )
    permission2 = UmaPermission(
        name=make_permission_name(portfolio, group),
        groups=[group.path],
        scopes=[
            make_scope(portfolio, Portfolio.KEYCLOAK_ACTIONS[0]),
        ],
    )
    client_mock.find_permissions_by_resource.return_value = [
        permission1,
        permission2,
    ]

    response = api_request("get", "catalog:portfolio-share-info", portfolio.id)

    assert response.status_code == 200
    shares = json.loads(response.content)
    assert (len(shares)) == 1
    assert shares[0]["group_id"] == group.id
    assert shares[0]["group_name"] == group.name
    assert (
        shares[0]["permissions"].sort()
        == [
            Portfolio.KEYCLOAK_ACTIONS[0],
            Portfolio.KEYCLOAK_ACTIONS[1],
        ].sort()
    )
    has_object_permission.assert_called_once()
    assert has_object_permission.call_args.args[3].id == portfolio.id
