""" Factory for catalog objects """
import factory

from main.catalog.models import (
    ApprovalRequest,
    Order,
    OrderItem,
    Portfolio,
    PortfolioItem,
    ProgressMessage,
)
from main.tests.factories import TenantFactory, UserFactory


class PortfolioFactory(factory.django.DjangoModelFactory):
    """Portfolio Factory"""

    class Meta:
        model = Portfolio

    tenant = factory.SubFactory(TenantFactory)
    name = factory.Sequence(lambda n: f"portfolio{n}")
    description = factory.Sequence(lambda n: f"portfolio{n}_description")


class PortfolioItemFactory(factory.django.DjangoModelFactory):
    """Portfolio Item Factory"""

    class Meta:
        model = PortfolioItem

    tenant = factory.SubFactory(TenantFactory)
    portfolio = factory.SubFactory(PortfolioFactory, tenant=tenant)
    name = factory.Sequence(lambda n: f"portfolio_item{n}")
    description = factory.Sequence(lambda n: f"portfolio_item{n}_description")
    service_offering_ref = factory.Sequence(lambda n: f"service_offering_{n}")


class OrderFactory(factory.django.DjangoModelFactory):
    """Order Factory"""

    class Meta:
        model = Order

    tenant = factory.SubFactory(TenantFactory)
    user = factory.SubFactory(UserFactory)


class OrderItemFactory(factory.django.DjangoModelFactory):
    """OrderItem Factory"""

    class Meta:
        model = OrderItem

    tenant = factory.SubFactory(TenantFactory)
    order = factory.SubFactory(OrderFactory, tenant=tenant)
    portfolio_item = factory.SubFactory(PortfolioItemFactory, tenant=tenant)
    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"order_item{n}")


class ApprovalRequestFactory(factory.django.DjangoModelFactory):
    """ApprovalRequest Factory"""

    class Meta:
        model = ApprovalRequest

    tenant = factory.SubFactory(TenantFactory)
    order = factory.SubFactory(OrderFactory, tenant=tenant)
    reason = factory.Sequence(lambda n: f"reason_{n}")
    approval_request_ref = factory.Sequence(
        lambda n: f"approval_request_ref{n}"
    )


class ProgressMessageFactory(factory.django.DjangoModelFactory):
    """ProgressMessage Factory"""

    class Meta:
        model = ProgressMessage

    tenant = factory.SubFactory(TenantFactory)
    message = factory.Sequence(lambda n: f"message_{n}")
