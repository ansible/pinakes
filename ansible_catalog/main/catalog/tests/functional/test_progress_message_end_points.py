""" Test order end points """
import json
import pytest
from django.urls import reverse

from ansible_catalog.main.catalog.tests.factories import OrderFactory
from ansible_catalog.main.catalog.tests.factories import OrderItemFactory


@pytest.mark.django_db
def test_order_progress_message_get(api_request):
    """Get List of Progress Messages of an order"""
    order = OrderFactory()
    order.update_message("Info", "test order message")

    response = api_request(
        "get", reverse("order-progressmessage-list", args=(order.id,))
    )

    assert response.status_code == 200

    content = json.loads(response.content)
    assert content["count"] == 1

    entry = content["results"][0]
    assert entry["message"] == "test order message"
    assert entry["messageable_type"] == "Order"


@pytest.mark.django_db
def test_order_item_progress_message_get(api_request):
    """Get List of Progress Messages of an order"""
    order_item = OrderItemFactory()
    order_item.update_message("Info", "test order item message")

    response = api_request(
        "get", reverse("orderitem-progressmessage-list", args=(order_item.id,))
    )

    assert response.status_code == 200

    content = json.loads(response.content)
    assert content["count"] == 1

    entry = content["results"][0]
    assert entry["message"] == "test order item message"
    assert entry["messageable_type"] == "OrderItem"
