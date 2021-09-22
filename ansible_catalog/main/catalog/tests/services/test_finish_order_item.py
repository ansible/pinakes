""" Test module for finishing an OrderItem """
import pytest
from ansible_catalog.main.catalog.tests.factories import OrderItemFactory
from ansible_catalog.main.catalog.models import OrderItem
from ansible_catalog.main.catalog.services.finish_order_item import (
    FinishOrderItem,
)


@pytest.mark.django_db
def test_finish_order_item_failed():
    """Test starting an order item"""
    job_id = "abcdef"
    order_item = OrderItemFactory(inventory_task_ref=job_id)
    FinishOrderItem(inventory_task_ref=job_id, error_msg="Kaboom").process()
    order_item.refresh_from_db()
    assert order_item.state == OrderItem.State.FAILED


@pytest.mark.django_db
def test_finish_order_item_success():
    """Test starting an order item"""
    job_id = "abcdef"
    order_item = OrderItemFactory(inventory_task_ref=job_id)
    FinishOrderItem(
        inventory_task_ref=job_id, artifacts={"abc": 123}
    ).process()
    order_item.refresh_from_db()
    assert order_item.state == OrderItem.State.COMPLETED
