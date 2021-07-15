""" Test on OrderItem """
import pytest
from django.db import IntegrityError

from catalog.tests.factories import (
    TenantFactory,
    UserFactory,
    OrderFactory,
    OrderItemFactory,
    PortfolioItemFactory
)


@pytest.mark.django_db
def test_orderitem():
    """ Test order item creation """
    tenant = TenantFactory()
    user = UserFactory()
    order = OrderFactory(tenant=tenant, user=user)
    user = UserFactory()
    order_item = OrderItemFactory(tenant=tenant, user=user, order=order)
    assert tenant.id == order_item.tenant.id
    assert order_item.state == order_item.state.CREATED

@pytest.mark.django_db
def test_empty_orderitem_name():
    """ Test empty name constraint on order item """

    tenant = TenantFactory()
    user = UserFactory()
    order = OrderFactory(tenant=tenant, user=user)
    with pytest.raises(IntegrityError) as excinfo:
        OrderItemFactory(tenant=tenant, user=user, order=order, name="")

    assert "CHECK constraint failed: catalog_orderitem_name_empty" in str(
        excinfo.value
    )

@pytest.mark.django_db
def test_duplicate_orderitem_name():
    """ Test duplicate names constraint on order item """

    tenant = TenantFactory()
    order = OrderFactory(tenant=tenant)
    portfolio_item = PortfolioItemFactory(tenant=tenant)
    name = "fred"
    OrderItemFactory(tenant=tenant, order=order, portfolio_item=portfolio_item, name=name)
    with pytest.raises(IntegrityError) as excinfo:
        OrderItemFactory(tenant=tenant, order=order, portfolio_item=portfolio_item, name=name)

    assert "UNIQUE constraint failed: catalog_orderitem.name" in str(
        excinfo.value
    )
