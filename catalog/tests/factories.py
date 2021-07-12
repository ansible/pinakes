import factory

from catalog.basemodel import Tenant
from catalog.models import (
    Portfolio,
    PortfolioItem,
    Order,
    OrderItem
)


class TenantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tenant

    external_tenant = factory.Sequence(lambda n: f"external{n}")


class PortfolioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Portfolio

    tenant = factory.SubFactory(TenantFactory)
    name = factory.Sequence(lambda n: f"portfolio{n}")
    description = factory.Sequence(lambda n: f"portfolio{n}_description")


class PortfolioItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PortfolioItem

    tenant = factory.SubFactory(TenantFactory)
    portfolio = factory.SubFactory(PortfolioFactory, tenant=tenant)
    name = factory.Sequence(lambda n: f"portfolio_item{n}")
    description = factory.Sequence(lambda n: f"portfolio_item{n}_description")
    service_offering_ref = factory.Sequence(lambda n: f"service_offering_{n}")


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    tenant = factory.SubFactory(TenantFactory)


class OrderItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderItem

    tenant = factory.SubFactory(TenantFactory)
    order = factory.SubFactory(OrderFactory, tenant=tenant)
    portfolio_item = factory.SubFactory(PortfolioItemFactory, tenant=tenant)
    name = factory.Sequence(lambda n: f"order_item{n}")
