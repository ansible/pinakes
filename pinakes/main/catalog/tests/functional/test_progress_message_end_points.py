"""Test order end points"""
import json
import pytest

from pinakes.main.catalog.permissions import ProgressMessagePermission
from pinakes.main.catalog.tests.factories import (
    OrderFactory,
)
from pinakes.main.catalog.tests.factories import (
    OrderItemFactory,
)


@pytest.mark.django_db
def test_order_progress_message_get(api_request, mocker):
    """Get List of Progress Messages of an order"""
    perform_check_object_permission = mocker.spy(
        ProgressMessagePermission, "perform_check_permission"
    )
    order = OrderFactory()
    order.update_message("Info", "test order message")
    response = api_request(
        "get", "catalog:order-progressmessage-list", order.id
    )

    assert response.status_code == 200

    content = json.loads(response.content)
    assert content["count"] == 1

    entry = content["results"][0]
    assert entry["message"] == "test order message"
    assert entry["messageable_type"] == "Order"

    perform_check_object_permission.assert_called()


@pytest.mark.django_db
def test_order_item_progress_message_get(api_request, mocker):
    """Get List of Progress Messages of an order"""
    perform_check_object_permission = mocker.spy(
        ProgressMessagePermission, "perform_check_permission"
    )
    order_item = OrderItemFactory()
    order_item.update_message("Info", "test order item message")

    response = api_request(
        "get", "catalog:orderitem-progressmessage-list", order_item.id
    )

    assert response.status_code == 200

    content = json.loads(response.content)
    assert content["count"] == 1

    entry = content["results"][0]
    assert entry["message"] == "test order item message"
    assert entry["messageable_type"] == "OrderItem"

    perform_check_object_permission.assert_called()
