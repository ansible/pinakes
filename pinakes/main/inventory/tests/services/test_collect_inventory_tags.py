"""Module to test Collection of inventory tags"""
import pytest
from pinakes.main.inventory.tests.factories import (
    ServiceInventoryFactory,
    ServiceOfferingFactory,
    ServiceOfferingNodeFactory,
    OfferingKind,
)
from pinakes.main.inventory.services.collect_inventory_tags import (
    CollectInventoryTags,
)


@pytest.mark.django_db
def test_single_service_offering():
    """Test to collect inventory tags from a single service offering"""

    service_inventory = ServiceInventoryFactory()
    service_offering = ServiceOfferingFactory(
        kind=OfferingKind.JOB_TEMPLATE, service_inventory=service_inventory
    )
    service_inventory.tags.add("/abc")
    obj = CollectInventoryTags(service_offering.id)
    obj.process()

    assert obj.tags()[0] == "/abc"


@pytest.mark.django_db
def test_single_service_offering_workflow():
    """Test to collect inventory tags from a single service offering"""

    service_inventory = ServiceInventoryFactory()
    service_inventory.tags.add("/abc")
    so1 = ServiceOfferingFactory(
        kind=OfferingKind.WORKFLOW, service_inventory=service_inventory
    )
    so2 = ServiceOfferingFactory(
        kind=OfferingKind.JOB_TEMPLATE, service_inventory=service_inventory
    )
    ServiceOfferingNodeFactory(root_service_offering=so1, service_offering=so1)
    ServiceOfferingNodeFactory(root_service_offering=so1, service_offering=so2)
    obj = CollectInventoryTags(so1.id)
    obj.process()
    assert len(obj.tags()) == 1
    assert obj.tags()[0] == "/abc"


@pytest.mark.django_db
def test_missing_service_offering():
    """Test to collect inventory tags from a missing service offering"""

    with pytest.raises(RuntimeError) as excinfo:
        CollectInventoryTags(9999).process()
    assert "ServiceOffering object 9999 not found" in str(excinfo.value)


@pytest.mark.django_db
def test_service_offering_with_no_inventory_tags():
    """Test to collect inventory tags service offering
    with no attached inventory tags"""

    service_inventory = ServiceInventoryFactory()
    service_offering = ServiceOfferingFactory(
        kind=OfferingKind.JOB_TEMPLATE, service_inventory=service_inventory
    )
    obj = CollectInventoryTags(service_offering.id)
    obj.process()

    assert len(obj.tags()) == 0


@pytest.mark.django_db
def test_service_offering_with_no_inventory():
    """Test to collect inventory tags service offering with no inventory"""

    service_offering = ServiceOfferingFactory(kind=OfferingKind.JOB_TEMPLATE)
    obj = CollectInventoryTags(service_offering.id)
    obj.process()

    assert len(obj.tags()) == 0
