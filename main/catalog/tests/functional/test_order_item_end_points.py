""" Module to test OrderItem end points """
import json
import pytest
from django.urls import reverse
from main.catalog.tests.factories import (
    OrderFactory,
    OrderItemFactory,
    PortfolioItemFactory
)


@pytest.mark.django_db
def test_order_item_list(api_request):
    """Get list of Order Items"""
    OrderItemFactory()
    response = api_request("get", reverse("orderitem-list"))

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1


@pytest.mark.django_db
def test_order_item_retrieve(api_request):
    """Retrieve a single order item by id"""
    order_item = OrderItemFactory()
    response = api_request(
        "get", reverse("orderitem-detail", args=(order_item.id,))
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == order_item.id
    assert content["owner"] == order_item.owner


@pytest.mark.django_db
def test_order_item_delete(api_request):
    """Delete a OrderItem by id"""
    order_item = OrderItemFactory()
    response = api_request(
        "delete", reverse("orderitem-detail", args=(order_item.id,))
    )

    assert response.status_code == 204


@pytest.mark.django_db
def test_order_item_post(api_request):
    """Create a new order item for a order"""
    order = OrderFactory()
    portfolio_item = PortfolioItemFactory()
    data = {
        "order": order.id,
        "portfolio_item": portfolio_item.id,
        "name": "abcdef",
    }
    response = api_request("post", reverse("orderitem-list"), data)
    assert response.status_code == 201


@pytest.mark.django_db
def test_order_item_patch(api_request):
    """PATCH on order item is not supported"""
    order_item = OrderItemFactory()
    data = {"name": "update"}
    response = api_request(
        "patch",
        reverse("orderitem-detail", args=(order_item.id,)),
        data,
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_order_item_put(api_request):
    """PUT on order item is not supported"""
    order_item = OrderItemFactory()
    data = {"name": "update"}
    response = api_request(
        "put", reverse("orderitem-detail", args=(order_item.id,)), data
    )

    assert response.status_code == 405
