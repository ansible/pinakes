import factory

from approval.basemodel import Tenant
from approval.models import Template
from approval.models import Workflow


class TenantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tenant

    external_tenant = factory.Sequence(lambda n: f"external{n}")


class TemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Template

    tenant = factory.SubFactory(TenantFactory)
    title = factory.Sequence(lambda n: f"title{n}")
    description = factory.Sequence(lambda n: f"title{n}_description")


class WorkflowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Workflow

    tenant = factory.SubFactory(TenantFactory)
    template = factory.SubFactory(TemplateFactory, tenant=tenant)
    name = factory.Sequence(lambda n: f"workflow{n}")
    description = factory.Sequence(lambda n: f"workflow{n}_description")
