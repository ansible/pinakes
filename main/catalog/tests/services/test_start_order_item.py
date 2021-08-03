""" Test module for starting an OrderItem """
from unittest.mock import patch
import pytest
from main.catalog.tests.factories import OrderItemFactory
from main.catalog.models import OrderItem
from main.catalog.services.start_order_item import StartOrderItem


@patch("main.catalog.services.start_order_item.StartTowerJob", autoSpec=True)
@pytest.mark.django_db
def test_start_order_item(mock):
    """Test starting an order item"""
    order_item = OrderItemFactory()
    job_id = "abcdef"
    mock.return_value.process.return_value = job_id
    StartOrderItem(order_item).process()
    order_item.refresh_from_db()
    assert order_item.state == OrderItem.State.ORDERED
    assert order_item.inventory_task_ref == job_id
