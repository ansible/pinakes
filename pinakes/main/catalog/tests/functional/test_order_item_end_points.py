"""Module to test OrderItem end points"""
import json
import pytest

from pinakes.main.catalog.permissions import OrderItemPermission
from pinakes.main.catalog.tests.factories import (
    OrderItemFactory,
    PortfolioItemFactory,
)

# FIXME(cutwater): Add unit tests for `catalog:orderitem-list` endpoint.

EXPECTED_USER_CAPABILITIES = {
    "retrieve": True,
    "update": True,
    "partial_update": True,
    "destroy": True,
}


@pytest.mark.django_db
def test_order_item_retrieve(api_request, mocker):
    """Retrieve a single order item by id"""
    has_object_permission = mocker.spy(
        OrderItemPermission, "has_object_permission"
    )
    order_item = OrderItemFactory()
    response = api_request("get", "catalog:orderitem-detail", order_item.id)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == order_item.id
    assert content["owner"] == order_item.owner
    assert content["extra_data"] is None
    assert (
        content["metadata"]["user_capabilities"] == EXPECTED_USER_CAPABILITIES
    )

    has_object_permission.assert_called_once()


@pytest.mark.django_db
def test_order_item_retrieve_extra(api_request, mocker):
    """Retrieve a single order item by id with param extra=true"""
    has_object_permission = mocker.spy(
        OrderItemPermission, "has_object_permission"
    )
    portfolio_item = PortfolioItemFactory()
    order_item = OrderItemFactory(portfolio_item=portfolio_item)
    response = api_request(
        "get",
        "catalog:orderitem-detail",
        order_item.id,
        data={"extra": "true"},
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == order_item.id
    assert content["owner"] == order_item.owner
    assert (
        content["extra_data"]["portfolio_item"]["name"] == portfolio_item.name
    )
    assert (
        content["metadata"]["user_capabilities"] == EXPECTED_USER_CAPABILITIES
    )
    has_object_permission.assert_called_once()


@pytest.mark.django_db
def test_order_item_delete(api_request, mocker):
    """Delete a OrderItem by id"""
    has_object_permission = mocker.spy(
        OrderItemPermission, "has_object_permission"
    )
    order_item = OrderItemFactory()
    response = api_request("delete", "catalog:orderitem-detail", order_item.id)

    assert response.status_code == 204
    has_object_permission.assert_called_once()


@pytest.mark.django_db
def test_order_item_patch(api_request):
    """PATCH on order item is not supported"""
    order_item = OrderItemFactory()
    data = {"name": "update"}
    response = api_request(
        "patch",
        "catalog:orderitem-detail",
        order_item.id,
        data,
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_order_item_put(api_request):
    """PUT on order item is not supported"""
    order_item = OrderItemFactory()
    data = {"name": "update"}
    response = api_request(
        "put", "catalog:orderitem-detail", order_item.id, data
    )

    assert response.status_code == 405
