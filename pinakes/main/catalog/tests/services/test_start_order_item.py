"""Start ordering an item"""

import pytest
from unittest import mock

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
from pinakes.main.catalog.services.sanitize_parameters import (
    SanitizeParameters,
)
from pinakes.main.catalog.services.compute_runtime_parameters import (
    ComputeRuntimeParameters,
)
from pinakes.main.catalog.tests.factories import (
    OrderFactory,
    OrderItemFactory,
    ServicePlanFactory,
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
        == "Submitting Order Item %(item_id)s for provisioning"
    )


@pytest.mark.django_db
def test_place_order_item_raise_provisioning_error(mocker):
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


@pytest.mark.django_db
def test_place_order_item_raise_validation_error(mocker):
    order = OrderFactory()
    order_item = OrderItemFactory(state=OrderItem.State.PENDING, order=order)

    mocker.patch(
        "pinakes.main.catalog.services.validate_order_item",
        side_effect=Exception("mocker error"),
    )
    svc = StartOrderItem(order)
    svc.process()
    order_item.refresh_from_db()

    assert order_item.state == Order.State.FAILED


@pytest.mark.django_db
def test_place_order_item_runtime_substitution(mocker):
    service_params = {"key": "val"}
    substituted_params = {"key": "sub"}
    order = OrderFactory()
    order_item = OrderItemFactory(
        state=OrderItem.State.PENDING,
        order=order,
        service_parameters=service_params,
        inventory_service_plan_ref="1",
    )
    ServicePlanFactory(inventory_service_plan_ref="1", base_schema={})

    mocker.patch.object(
        ComputeRuntimeParameters,
        "process",
        return_value=mock.Mock(
            substituted=True, runtime_parameters=substituted_params
        ),
    )
    mocker.patch.object(
        SanitizeParameters,
        "process",
        return_value=mock.Mock(sanitized_parameters=substituted_params),
    )
    mocker.patch.object(ProvisionOrderItem, "process", return_value=None)
    StartOrderItem(order).process()
    order_item.refresh_from_db()

    assert order_item.service_parameters == substituted_params


@pytest.mark.django_db
def test_place_order_item_runtime_substitution_secret(mocker):
    service_params = {"key": "val"}
    substituted_params = {"key": "sub"}
    hidden_params = {"key": "$secret"}
    order = OrderFactory()
    order_item = OrderItemFactory(
        state=OrderItem.State.PENDING,
        order=order,
        service_parameters=service_params,
        inventory_service_plan_ref="1",
    )
    ServicePlanFactory(inventory_service_plan_ref="1", base_schema={})

    mocker.patch.object(
        ComputeRuntimeParameters,
        "process",
        return_value=mock.Mock(
            substituted=True, runtime_parameters=substituted_params
        ),
    )
    mocker.patch.object(
        SanitizeParameters,
        "process",
        return_value=mock.Mock(sanitized_parameters=hidden_params),
    )
    mocker.patch.object(ProvisionOrderItem, "process", return_value=None)
    StartOrderItem(order).process()
    order_item.refresh_from_db()
    assert order_item.service_parameters == hidden_params
    assert order_item.service_parameters_raw == substituted_params
