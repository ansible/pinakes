"""Test on Order"""
import pytest

from pinakes.main.catalog.models import ProgressMessage

from pinakes.main.catalog.tests.factories import (
    OrderFactory,
)
from pinakes.main.tests.factories import TenantFactory
from pinakes.main.tests.factories import UserFactory


@pytest.mark.django_db
def test_order():
    """Test on Order Creation"""
    tenant = TenantFactory()
    user = UserFactory()

    order = OrderFactory(tenant=tenant, user=user)
    assert tenant.id == order.tenant.id
    assert order.state == order.state.CREATED


@pytest.mark.django_db
def test_update_message():
    """Test update_message on an order"""
    tenant = TenantFactory()
    user = UserFactory()

    order = OrderFactory(tenant=tenant, user=user)
    order.update_message("Info", "test order update message")

    assert ProgressMessage.objects.all().count() == 1

    progress_message = ProgressMessage.objects.first()

    assert progress_message.message == "test order update message"
    assert progress_message.level == "Info"
    assert progress_message.messageable_id == order.id
    assert progress_message.messageable_type == "Order"


@pytest.mark.django_db
def test_mark_completed():
    """Test mark_completed on an order"""
    tenant = TenantFactory()
    user = UserFactory()

    order = OrderFactory(tenant=tenant, user=user)
    assert order.state == "Created"

    order.mark_completed("completed")
    order.refresh_from_db()

    assert order.state == "Completed"
    assert ProgressMessage.objects.all().count() == 1
    assert ProgressMessage.objects.first().message == "completed"
    assert ProgressMessage.objects.first().messageable_type == "Order"
    assert ProgressMessage.objects.first().messageable_id == order.id


@pytest.mark.django_db
def test_mark_canceled():
    """Test mark_canceled on an order"""
    tenant = TenantFactory()
    user = UserFactory()

    order = OrderFactory(tenant=tenant, user=user)
    assert order.state == "Created"

    order.mark_canceled("canceled")
    order.refresh_from_db()

    assert order.state == "Canceled"
    assert ProgressMessage.objects.all().count() == 1
    assert ProgressMessage.objects.first().message == "canceled"
    assert ProgressMessage.objects.first().messageable_type == "Order"
    assert ProgressMessage.objects.first().messageable_id == order.id
