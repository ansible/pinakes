""" Module to test OrderItem end points """
import json
import pytest
from ansible_catalog.main.catalog.tests.factories import OrderItemFactory


@pytest.mark.django_db
def test_order_item_retrieve(api_request):
    """Retrieve a single order item by id"""
    order_item = OrderItemFactory()
    response = api_request("get", "orderitem-detail", order_item.id)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == order_item.id
    assert content["owner"] == order_item.owner


@pytest.mark.django_db
def test_order_item_delete(api_request):
    """Delete a OrderItem by id"""
    order_item = OrderItemFactory()
    response = api_request("delete", "orderitem-detail", order_item.id)

    assert response.status_code == 204


@pytest.mark.django_db
def test_order_item_patch(api_request):
    """PATCH on order item is not supported"""
    order_item = OrderItemFactory()
    data = {"name": "update"}
    response = api_request(
        "patch",
        "orderitem-detail",
        order_item.id,
        data,
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_order_item_put(api_request):
    """PUT on order item is not supported"""
    order_item = OrderItemFactory()
    data = {"name": "update"}
    response = api_request("put", "orderitem-detail", order_item.id, data)

    assert response.status_code == 405
