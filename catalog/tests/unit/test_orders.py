""" Test on Order """
import pytest

from catalog.tests.factories import OrderFactory
from catalog.tests.factories import TenantFactory
from catalog.tests.factories import UserFactory


@pytest.mark.django_db
def test_order():
    """ Test on Order Creation """
    tenant = TenantFactory()
    user = UserFactory()

    order = OrderFactory(tenant=tenant, user=user)
    assert tenant.id == order.tenant.id
    assert order.state == order.state.CREATED
