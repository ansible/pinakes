""" Test module for finishing an OrderItem """
import pytest
from main.catalog.tests.factories import OrderItemFactory
from main.catalog.models import OrderItem
from main.catalog.services.finish_order_item import FinishOrderItem


@pytest.mark.django_db
def test_finish_order_item_failed():
    """Test starting an order item"""
    job_id = "abcdef"
    order_item = OrderItemFactory(inventory_task_ref=job_id)
    FinishOrderItem(job_id, {}, "Kaboom").process()
    order_item.refresh_from_db()
    assert order_item.state == OrderItem.State.FAILED


@pytest.mark.django_db
def test_finish_order_item_success():
    """Test starting an order item"""
    job_id = "abcdef"
    order_item = OrderItemFactory(inventory_task_ref=job_id)
    FinishOrderItem(job_id, {"abc": 123}, None).process()
    order_item.refresh_from_db()
    assert order_item.state == OrderItem.State.COMPLETED
