""" Test order end points """
import json
import pytest

from ansible_catalog.main.catalog.tests.factories import (
    OrderFactory,
    OrderItemFactory,
    PortfolioFactory,
    PortfolioItemFactory,
)
from ansible_catalog.main.inventory.tests.factories import (
    ServiceOfferingFactory,
)


@pytest.mark.django_db
def test_order_list(api_request):
    """Get List of Orders"""
    OrderFactory()
    response = api_request("get", "order-list")

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1


@pytest.mark.django_db
def test_order_retrieve(api_request):
    """Retrieve a single order by id"""
    order = OrderFactory()
    response = api_request("get", "order-detail", order.id)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == order.id
    assert content["owner"] == order.owner


@pytest.mark.django_db
def test_order_delete(api_request):
    """Delete a single order by id"""
    order = OrderFactory()
    response = api_request("delete", "order-detail", order.id)

    assert response.status_code == 204


@pytest.mark.django_db
def test_order_submit(api_request, mocker):
    """Submit a single order by id"""
    service_offering = ServiceOfferingFactory()
    portfolio = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(
        portfolio=portfolio, service_offering_ref=service_offering.id
    )
    order = OrderFactory()
    OrderItemFactory(order=order, portfolio_item=portfolio_item)

    mocker.patch("django_rq.enqueue")

    assert (order.state) == "Created"

    response = api_request("post", "order-submit", order.id)
    order.refresh_from_db()

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["state"] == "Pending"
    assert content["state"] == order.state


@pytest.mark.django_db
def test_order_submit_without_service_offering(api_request):
    """Submit a single order by id"""
    portfolio = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(portfolio=portfolio)
    order = OrderFactory()
    OrderItemFactory(order=order, portfolio_item=portfolio_item)

    response = api_request("post", "order-submit", order.id)

    assert response.status_code == 400
    content = json.loads(response.content)
    assert (
        content["detail"]
        == "Portfolio item %d does not have related service offering"
        % portfolio_item.id
    )


@pytest.mark.django_db
def test_order_submit_without_order_item(api_request):
    """Submit a single order by id"""
    portfolio = PortfolioFactory()
    PortfolioItemFactory(portfolio=portfolio)
    order = OrderFactory()

    response = api_request("post", "order-submit", order.id)

    assert response.status_code == 400
    content = json.loads(response.content)
    assert (
        content["detail"]
        == "Order %d does not have related order items" % order.id
    )


@pytest.mark.django_db
def test_order_patch_not_supported(api_request):
    """Patch a single order by id"""
    order = OrderFactory()
    data = {"name": "update"}
    response = api_request("patch", "order-detail", order.id, data)

    assert response.status_code == 405


@pytest.mark.django_db
def test_order_put_not_supported(api_request):
    """PUT is not supported"""
    order = OrderFactory()
    data = {"name": "update"}
    response = api_request("put", "order-detail", order.id, data)

    assert response.status_code == 405


@pytest.mark.django_db
def test_order_post(api_request):
    """Create a Order"""
    data = {"name": "abcdef", "description": "abc"}
    response = api_request("post", "order-list", data=data)
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

    response = api_request("get", "order-orderitem-list", order2.id)

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1
    assert content["results"][0]["id"] == order_item.id


@pytest.mark.django_db
def test_order_order_item_post(api_request):
    """Create a new order item from an order"""
    order = OrderFactory()
    portfolio_item = PortfolioItemFactory()
    data = {
        "order": order.id,  # TODO: remove order from data
        "portfolio_item": portfolio_item.id,
        "name": "abcdef",
    }
    response = api_request("post", "order-orderitem-list", order.id, data)
    assert response.status_code == 201
