"""Factory for the Inventory objects"""
import factory
from django.utils import timezone
from pinakes.main.models import Source
from pinakes.main.tests.factories import default_tenant
from pinakes.main.inventory.models import (
    ServiceInstance,
    ServiceInventory,
)
from pinakes.main.inventory.models import (
    ServiceOffering,
    OfferingKind,
)
from pinakes.main.inventory.models import (
    InventoryServicePlan,
)
from pinakes.main.inventory.models import (
    ServiceOfferingNode,
)


class SourceFactory(factory.django.DjangoModelFactory):
    """Source Factory"""

    class Meta:
        model = Source

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    name = factory.Sequence(lambda n: f"source{n}")


class ServiceInventoryFactory(factory.django.DjangoModelFactory):
    """ServiceInventory Factory"""

    class Meta:
        model = ServiceInventory

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    source = factory.SubFactory(SourceFactory)
    name = factory.Sequence(lambda n: f"inventory{n}")
    source_created_at = timezone.now()
    source_updated_at = timezone.now()
    source_ref = factory.Sequence(lambda n: f"{n}")
    extra = {}


class ServiceOfferingFactory(factory.django.DjangoModelFactory):
    """ServiceOffering Factory"""

    class Meta:
        model = ServiceOffering

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    source = factory.SubFactory(SourceFactory)
    service_inventory = factory.SubFactory(
        ServiceInventoryFactory, tenant=tenant, source=source
    )
    name = factory.Sequence(lambda n: f"service_offering{n}")
    source_created_at = timezone.now()
    source_updated_at = timezone.now()
    survey_enabled = False
    kind = OfferingKind.JOB_TEMPLATE
    source_ref = factory.Sequence(lambda n: f"{n}")
    extra = {}


class InventoryServicePlanFactory(factory.django.DjangoModelFactory):
    """InventoryServicePlan Factory"""

    class Meta:
        model = InventoryServicePlan

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    source = factory.SubFactory(SourceFactory)
    service_offering = factory.SubFactory(
        ServiceOfferingFactory,
        tenant=tenant,
        source=source,
        survey_enabled=True,
    )
    name = factory.Sequence(lambda n: f"service_plan{n}")
    source_created_at = timezone.now()
    source_updated_at = timezone.now()
    source_ref = factory.Sequence(lambda n: f"{n}")
    extra = {}
    create_json_schema = {}


class ServiceOfferingNodeFactory(factory.django.DjangoModelFactory):
    """ServiceOfferingNode Factory"""

    class Meta:
        model = ServiceOfferingNode

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    source = factory.SubFactory(SourceFactory)
    service_offering = factory.SubFactory(
        ServiceOfferingFactory,
        tenant=tenant,
        source=source,
        survey_enabled=True,
    )
    root_service_offering = factory.SubFactory(
        ServiceOfferingFactory,
        tenant=tenant,
        source=source,
        survey_enabled=True,
    )
    source_created_at = timezone.now()
    source_updated_at = timezone.now()
    source_ref = factory.Sequence(lambda n: f"{n}")
    extra = {}


class ServiceInstanceFactory(factory.django.DjangoModelFactory):
    """ServiceInstance Factory"""

    class Meta:
        model = ServiceInstance

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    source = factory.SubFactory(SourceFactory)
    service_offering = factory.SubFactory(
        ServiceOfferingFactory,
        tenant=tenant,
        source=source,
        survey_enabled=True,
    )
    service_plan = factory.SubFactory(
        InventoryServicePlanFactory,
        tenant=tenant,
        source=source,
    )
    service_inventory = factory.SubFactory(
        ServiceInventoryFactory,
        tenant=tenant,
        source=source,
    )
    name = factory.Sequence(lambda n: f"service_instance{n}")
    source_created_at = timezone.now()
    source_updated_at = timezone.now()
    extra = {}
