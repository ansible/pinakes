"""Test module for finishing an OrderItem"""
import pytest
from pinakes.main.catalog.tests.factories import (
    OrderItemFactory,
)
from pinakes.main.catalog.models import OrderItem
from pinakes.main.catalog.services.finish_order_item import (
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
    service_instance_ref = "instance_ref"
    external_url = "/api/v1/job/123"
    order_item = OrderItemFactory(inventory_task_ref=job_id)

    FinishOrderItem(
        inventory_task_ref=job_id,
        artifacts={"abc": 123},
        external_url=external_url,
        service_instance_ref=service_instance_ref,
    ).process()

    order_item.refresh_from_db()
    assert order_item.state == OrderItem.State.COMPLETED
    assert order_item.external_url == external_url
    assert order_item.service_instance_ref == service_instance_ref
    assert order_item.inventory_task_ref == job_id
