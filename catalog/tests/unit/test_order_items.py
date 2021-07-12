import pytest
import pdb

from catalog.tests.factories import (
    TenantFactory,
    OrderFactory,
    OrderItemFactory
)


class TestOrderItems:
    @pytest.mark.django_db
    def test_orderitem(self):
        tenant = TenantFactory()
        order = OrderFactory(tenant=tenant)
        order_item = OrderItemFactory(tenant=tenant, order=order)
        assert tenant.id == order_item.tenant.id

    @pytest.mark.django_db
    def test_empty_orderitem_name(self):
        from django.db import IntegrityError

        tenant = TenantFactory()
        order = OrderFactory(tenant=tenant)
        with pytest.raises(IntegrityError) as excinfo:
            OrderItemFactory(tenant=tenant, order=order, name="")

        assert "CHECK constraint failed: catalog_orderitem_name_empty" in str(
            excinfo.value
        )

    @pytest.mark.django_db
    def test_duplicate_orderitem_name(self):
        from django.db import IntegrityError

        tenant = TenantFactory()
        order = OrderFactory(tenant=tenant)
        name = "fred"
        OrderItemFactory(tenant=tenant, order=order, name=name)
        with pytest.raises(IntegrityError) as excinfo:
            OrderItemFactory(tenant=tenant, order=order, name=name)

        assert "UNIQUE constraint failed: catalog_orderitem.name" in str(
            excinfo.value
        )
