"""Collection of factory classes for approval models"""
import factory
from decimal import Decimal

from automation_services_catalog.main.approval.models import (
    Template,
    Workflow,
    Request,
    RequestContext,
    Action,
)
from automation_services_catalog.main.tests.factories import default_tenant


class TemplateFactory(factory.django.DjangoModelFactory):
    """Template factory class"""

    class Meta:
        model = Template

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    title = factory.Sequence(lambda n: f"title{n}")
    description = factory.Sequence(lambda n: f"title{n}_description")


class WorkflowFactory(factory.django.DjangoModelFactory):
    """Workflow factory class"""

    class Meta:
        model = Workflow

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    template = factory.SubFactory(TemplateFactory)
    name = factory.Sequence(lambda n: f"workflow{n}")
    description = factory.Sequence(lambda n: f"workflow{n}_description")
    internal_sequence = factory.Sequence(lambda n: Decimal(n))


class RequestFactory(factory.django.DjangoModelFactory):
    """Request factory class"""

    class Meta:
        model = Request

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    workflow = factory.SubFactory(WorkflowFactory)


class RequestContextFactory(factory.django.DjangoModelFactory):
    """RequestContext factory class"""

    class Meta:
        model = RequestContext

    context = {}


class ActionFactory(factory.django.DjangoModelFactory):
    """Action factory class"""

    class Meta:
        model = Action

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    request = factory.SubFactory(RequestFactory)
