""" Factory for catalog objects """
import factory

from main.catalog.models import (
    ApprovalRequest,
    CatalogServicePlan,
    Order,
    OrderItem,
    Portfolio,
    PortfolioItem,
    ProgressMessage,
)
from main.tests.factories import UserFactory, default_tenant


class PortfolioFactory(factory.django.DjangoModelFactory):
    """Portfolio Factory"""

    class Meta:
        model = Portfolio

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    name = factory.Sequence(lambda n: f"portfolio{n}")
    description = factory.Sequence(lambda n: f"portfolio{n}_description")


class PortfolioItemFactory(factory.django.DjangoModelFactory):
    """Portfolio Item Factory"""

    class Meta:
        model = PortfolioItem

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    portfolio = factory.SubFactory(PortfolioFactory)
    name = factory.Sequence(lambda n: f"portfolio_item{n}")
    description = factory.Sequence(lambda n: f"portfolio_item{n}_description")


class OrderFactory(factory.django.DjangoModelFactory):
    """Order Factory"""

    class Meta:
        model = Order

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    user = factory.SubFactory(UserFactory)


class OrderItemFactory(factory.django.DjangoModelFactory):
    """OrderItem Factory"""

    class Meta:
        model = OrderItem

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    order = factory.SubFactory(OrderFactory)
    portfolio_item = factory.SubFactory(PortfolioItemFactory)
    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"order_item{n}")


class ApprovalRequestFactory(factory.django.DjangoModelFactory):
    """ApprovalRequest Factory"""

    class Meta:
        model = ApprovalRequest

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    order = factory.SubFactory(OrderFactory)
    reason = factory.Sequence(lambda n: f"reason_{n}")
    approval_request_ref = factory.Sequence(
        lambda n: f"approval_request_ref{n}"
    )


class ProgressMessageFactory(factory.django.DjangoModelFactory):
    """ProgressMessage Factory"""

    class Meta:
        model = ProgressMessage

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    message = factory.Sequence(lambda n: f"message_{n}")


class ServicePlanFactory(factory.django.DjangoModelFactory):
    """Catalog ServicePlan Factory"""

    class Meta:
        model = CatalogServicePlan

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    portfolio_item = factory.SubFactory(PortfolioItemFactory)

    name = factory.Sequence(lambda n: f"catalog service_plan_{n}")
    description = factory.Sequence(
        lambda n: f"catalog_service_plan_{n}_description"
    )
