""" Start ordering an item """

import pytest

from pinakes.main.catalog.models import (
    Order,
    OrderItem,
    ProgressMessage,
)
from pinakes.main.catalog.services.start_order_item import (
    StartOrderItem,
)
from pinakes.main.catalog.services.provision_order_item import (
    ProvisionOrderItem,
)
from pinakes.main.catalog.tests.factories import (
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
    order_item = OrderItemFactory(state=OrderItem.State.PENDING, order=order)

    mocker.patch(
        "pinakes.main.catalog.services.provision_order_item",
        side_effect=Exception("mocker error"),
    )
    svc = StartOrderItem(order)
    svc.process()
    order_item.refresh_from_db()

    assert order_item.state == Order.State.FAILED
