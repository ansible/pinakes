import pytest

from catalog.tests.factories import OrderFactory
from catalog.tests.factories import TenantFactory


class TestOrders:
    @pytest.mark.django_db
    def test_order(self):
        tenant = TenantFactory()
        order = OrderFactory(tenant=tenant)
        assert tenant.id == order.tenant.id
