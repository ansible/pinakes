"""Test order end points"""
import json
import pytest

from pinakes.main.catalog.permissions import (
    OrderPermission,
    OrderItemPermission,
)
from pinakes.main.catalog.tests.factories import (
    OrderFactory,
    OrderItemFactory,
    PortfolioFactory,
    PortfolioItemFactory,
    ServicePlanFactory,
)
from pinakes.main.inventory.tests.factories import (
    ServiceOfferingFactory,
)


EXPECTED_USER_CAPABILITIES = {
    "retrieve": True,
    "destroy": True,
    "cancel": True,
    "submit": True,
}


@pytest.mark.django_db
def test_order_list(api_request, mocker):
    """Get List of Orders"""
    scope_queryset = mocker.spy(OrderPermission, "scope_queryset")
    OrderFactory()
    response = api_request("get", "catalog:order-list")

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1
    results = content["results"]
    assert results[0]["extra_data"] is None
    assert (
        results[0]["metadata"]["user_capabilities"]
        == EXPECTED_USER_CAPABILITIES
    )

    scope_queryset.assert_called_once()


@pytest.mark.django_db
def test_order_list_extra(api_request, mocker):
    """Get List of Orders with param extra=true"""
    scope_queryset = mocker.spy(OrderPermission, "perform_scope_queryset")
    OrderFactory()
    response = api_request("get", "catalog:order-list", data={"extra": "true"})

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1
    assert content["results"][0]["extra_data"]["order_items"] is not None
    scope_queryset.assert_called_once()


@pytest.mark.django_db
def test_order_retrieve(api_request, mocker):
    """Retrieve a single order by id"""
    check_object_permission = mocker.spy(
        OrderPermission, "perform_check_object_permission"
    )
    order = OrderFactory()
    response = api_request("get", "catalog:order-detail", order.id)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == order.id
    assert content["owner"] == order.owner
    assert content["extra_data"] is None
    assert (
        content["metadata"]["user_capabilities"] == EXPECTED_USER_CAPABILITIES
    )
    check_object_permission.assert_called()


@pytest.mark.django_db
def test_order_retrieve_extra(api_request, mocker):
    """Retrieve a single order by id with param extra=true"""
    check_object_permission = mocker.spy(
        OrderPermission, "perform_check_object_permission"
    )
    order = OrderFactory()
    order_item = OrderItemFactory(order=order)
    response = api_request(
        "get", "catalog:order-detail", order.id, data={"extra": "true"}
    )

    assert response.status_code == 200
    result = json.loads(response.content)
    assert result["id"] == order.id
    assert result["owner"] == order.owner

    order_item_result = result["extra_data"]["order_items"][0]
    assert order_item_result["name"] == order_item.name
    assert "user_capabilities" not in order_item_result
    check_object_permission.assert_called()


@pytest.mark.django_db
def test_order_delete(api_request, mocker):
    """Delete a single order by id"""
    check_object_permission = mocker.spy(
        OrderPermission, "perform_check_object_permission"
    )
    order = OrderFactory()
    response = api_request("delete", "catalog:order-detail", order.id)

    assert response.status_code == 204
    check_object_permission.assert_called()


@pytest.mark.django_db
def test_order_submit(api_request, mocker):
    """Submit a single order by id"""
    mocker.patch("django_rq.enqueue")
    check_object_permission = mocker.spy(
        OrderPermission, "perform_check_object_permission"
    )

    service_offering = ServiceOfferingFactory()
    portfolio = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(
        portfolio=portfolio, service_offering_ref=service_offering.id
    )
    order = OrderFactory()
    OrderItemFactory(order=order, portfolio_item=portfolio_item)

    assert order.state == "Created"

    response = api_request("post", "catalog:order-submit", order.id)
    order.refresh_from_db()

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["state"] == "Approval Pending"
    assert content["state"] == order.state
    check_object_permission.assert_called()


@pytest.mark.django_db
def test_order_submit_without_service_offering(api_request, mocker):
    """Submit a single order by id"""
    check_object_permission = mocker.spy(
        OrderPermission, "perform_check_object_permission"
    )
    portfolio = PortfolioFactory()
    portfolio_item = PortfolioItemFactory(portfolio=portfolio)
    order = OrderFactory()
    OrderItemFactory(order=order, portfolio_item=portfolio_item)

    response = api_request("post", "catalog:order-submit", order.id)

    assert response.status_code == 400
    content = json.loads(response.content)
    assert (
        content["detail"] == f"Portfolio item {portfolio_item.id} does not"
        " have related service offering"
    )
    check_object_permission.assert_called()


@pytest.mark.django_db
def test_order_submit_without_order_item(api_request, mocker):
    """Submit a single order by id"""
    check_object_permission = mocker.spy(
        OrderPermission, "perform_check_object_permission"
    )
    portfolio = PortfolioFactory()
    PortfolioItemFactory(portfolio=portfolio)
    order = OrderFactory()

    response = api_request("post", "catalog:order-submit", order.id)

    assert response.status_code == 400
    content = json.loads(response.content)
    assert (
        content["detail"]
        == f"Order {order.id} does not have related order items"
    )
    check_object_permission.assert_called()


@pytest.mark.django_db
def test_order_cancel(api_request, mocker):
    """Cancels a single order by id"""
    mocker.patch("django_rq.enqueue")
    check_object_permission = mocker.spy(
        OrderPermission, "perform_check_object_permission"
    )

    order = OrderFactory()

    assert order.state == "Created"

    response = api_request("patch", "catalog:order-cancel", order.id)
    order.refresh_from_db()

    assert response.status_code == 204
    assert order.state == "Canceled"
    check_object_permission.assert_called()


@pytest.mark.django_db
def test_order_cancel_with_uncancelable_states(api_request, mocker):
    """Cancels a single order by id"""
    mocker.patch("django_rq.enqueue")
    check_object_permission = mocker.spy(
        OrderPermission, "perform_check_object_permission"
    )

    order = OrderFactory(state="Completed")

    response = api_request("patch", "catalog:order-cancel", order.id)
    order.refresh_from_db()

    assert response.status_code == 400
    content = json.loads(response.content)
    assert content["detail"] == (
        "Order {} is not cancel able in its current state: {}"
    ).format(order.id, order.state)
    check_object_permission.assert_called_once()


@pytest.mark.django_db
def test_order_patch_not_supported(api_request):
    """Patch a single order by id"""
    order = OrderFactory()
    data = {"name": "update"}
    response = api_request("patch", "catalog:order-detail", order.id, data)

    assert response.status_code == 405


@pytest.mark.django_db
def test_order_put_not_supported(api_request):
    """PUT is not supported"""
    order = OrderFactory()
    data = {"name": "update"}
    response = api_request("put", "catalog:order-detail", order.id, data)

    assert response.status_code == 405


@pytest.mark.django_db
def test_order_post(api_request, mocker):
    """Create a Order"""
    check_permission = mocker.spy(OrderPermission, "perform_check_permission")
    data = {"name": "abcdef", "description": "abc"}
    response = api_request("post", "catalog:order-list", data=data)
    content = json.loads(response.content)

    assert response.status_code == 201
    assert content["owner"] == "Ansible Catalog"
    check_permission.assert_called_once()


@pytest.mark.django_db
def test_order_order_items_get(api_request, mocker):
    """List OrderItems by order id"""
    scope_queryset = mocker.spy(OrderItemPermission, "perform_scope_queryset")
    order1 = OrderFactory()
    order2 = OrderFactory()
    OrderItemFactory(order=order1)
    OrderItemFactory(order=order1)
    order_item = OrderItemFactory(order=order2)

    response = api_request("get", "catalog:order-orderitem-list", order2.id)

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1
    assert content["results"][0]["id"] == order_item.id
    scope_queryset.assert_called_once()


@pytest.mark.django_db
def test_order_order_item_post(api_request, mocker):
    """Create a new order item from an order"""
    perform_check_permission = mocker.spy(
        OrderItemPermission, "perform_check_permission"
    )
    order = OrderFactory()
    service_offering = ServiceOfferingFactory()
    portfolio_item = PortfolioItemFactory(
        service_offering_ref=service_offering.id
    )
    ServicePlanFactory(portfolio_item=portfolio_item)
    data = {"portfolio_item": portfolio_item.id, "service_parameters": {}}
    response = api_request(
        "post", "catalog:order-orderitem-list", order.id, data
    )
    content = response.data
    assert response.status_code == 201
    assert content["name"] == portfolio_item.name
    assert content["order"] == str(order.id)
    perform_check_permission.assert_called_once()

    response = api_request(
        "post", "catalog:order-orderitem-list", order.id, data
    )
    # uniqueness
    assert response.status_code == 400
