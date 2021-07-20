""" Test order end points """
import json
import pytest
from django.urls import reverse
from catalog.tests.factories import OrderFactory
from catalog.tests.factories import OrderItemFactory
from catalog.tests.factories import TenantFactory
from catalog.tests.factories import UserFactory


@pytest.mark.django_db
def test_order_list(api_request):
    """Get List of Orders"""
    OrderFactory()
    response = api_request("get", reverse("catalog:order-list"))

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1


@pytest.mark.django_db
def test_order_retrieve(api_request):
    """Retrieve a single order by id"""
    order = OrderFactory()
    response = api_request(
        "get", reverse("catalog:order-detail", args=(order.id,))
    )

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == order.id
    assert content["owner"] == order.owner


@pytest.mark.django_db
def test_order_delete(api_request):
    """Delete a single order by id"""
    order = OrderFactory()
    response = api_request(
        "delete", reverse("catalog:order-detail", args=(order.id,))
    )

    assert response.status_code == 204


@pytest.mark.django_db
def test_order_patch_not_supported(api_request):
    """Patch a single order by id"""
    order = OrderFactory()
    data = {"name": "update"}
    response = api_request(
        "patch", reverse("catalog:order-detail", args=(order.id,)), data
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_order_put_not_supported(api_request):
    """PUT is not supported"""
    order = OrderFactory()
    data = {"name": "update"}
    response = api_request(
        "put", reverse("catalog:order-detail", args=(order.id,)), data
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_order_post(api_request):
    """Create a Order"""
    TenantFactory()
    data = {"name": "abcdef", "description": "abc"}
    response = api_request("post", reverse("catalog:order-list"), data)
    content = json.loads(response.content)

    assert response.status_code == 201
    assert content["owner"] == "admin"

@pytest.mark.django_db
def test_order_order_items_get(api_request):
    """List OrderItems by order id"""
    order1 = OrderFactory()
    order2 = OrderFactory()
    OrderItemFactory(order=order1)
    OrderItemFactory(order=order1)
    order_item = OrderItemFactory(order=order2)

    response = api_request(
        "get", reverse("catalog:order-orderitem-list", args=(order2.id,))
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1
    assert content["results"][0]["id"] == order_item.id
