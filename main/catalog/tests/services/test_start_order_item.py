""" Start ordering an item """

import pytest

from main.approval.models import Request
from main.approval.tests.factories import RequestFactory

from main.catalog.models import (
    ApprovalRequest,
    Order,
    OrderItem,
    ProgressMessage,
)
from main.catalog.services.start_order_item import StartOrderItem
from main.catalog.services.provision_order_item import ProvisionOrderItem
from main.catalog.tests.factories import (
    ApprovalRequestFactory,
    OrderFactory,
    OrderItemFactory,
)


@pytest.mark.django_db
def test_place_order_item(mocker):
    order = OrderFactory()
    OrderItemFactory(state=OrderItem.State.PENDING, order=order)
    OrderItemFactory(state=OrderItem.State.APPROVED, order=order)

    mocker.patch.object(ProvisionOrderItem, "process", return_value=None)
    svc = StartOrderItem(order)
    svc.process()

    assert (
        str(ProgressMessage.objects.first())
        == "Submitting Order Item 1 for provisioning"
    )


@pytest.mark.django_db
def test_place_order_item_raise_error(mocker):
    order = OrderFactory()
    order_item_1 = OrderItemFactory(state=OrderItem.State.PENDING, order=order)
    order_item_2 = OrderItemFactory(state=OrderItem.State.PENDING, order=order)

    with mocker.patch(
        "main.catalog.services.provision_order_item",
        side_effect=Exception("mocker error"),
    ):
        svc = StartOrderItem(order)
        svc.process()
        order_item_1.refresh_from_db()
        order_item_2.refresh_from_db()

        assert order_item_1.state == Order.State.FAILED
        assert order_item_2.state == Order.State.FAILED
