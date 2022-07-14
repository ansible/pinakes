"""Collect Inventory Tags for a given service offering"""
from django.utils.translation import gettext_lazy as _
from pinakes.main.inventory.models import (
    ServiceOffering,
    ServiceOfferingNode,
    OfferingKind,
)


class CollectInventoryTags:
    """Collect Inventory Tags for a given service_offering_id"""

    def __init__(self, service_offering_id):
        self.service_offering_id = service_offering_id
        self.inventory_tags = []

    def process(self):
        """Process the nodes"""
        inventory_ids = set()
        visited = set()
        self._collect_inventory(
            self.service_offering_id, visited, inventory_ids
        )
        return self

    def tags(self):
        """Return the list of tags assigned to the given service_offering"""
        return self.inventory_tags

    def _collect_inventory(self, object_id, visited, inventory_ids):
        """Collect the Inventory ids for this node and its children"""
        if object_id in visited:
            return

        obj = ServiceOffering.objects.filter(id=object_id).first()
        if obj is None:
            raise RuntimeError(
                _("ServiceOffering object {} not found").format(object_id)
            )

        visited.add(object_id)
        if obj.service_inventory is not None:
            self._collect_tags(obj.service_inventory, inventory_ids)

        if obj.kind == OfferingKind.WORKFLOW:
            self._process_children(obj.id, visited, inventory_ids)

    def _process_children(self, root_id, visited, inventory_ids):
        """Collect Inventory objects for children"""
        for child in ServiceOfferingNode.objects.filter(
            root_service_offering_id=root_id
        ):
            if child.service_inventory is not None:
                self._collect_tags(child.service_inventory, inventory_ids)

            self._collect_inventory(
                child.service_offering_id, visited, inventory_ids
            )

    def _collect_tags(self, obj, inventory_ids):
        """COllect tags if the object has not been loaded yet"""
        if obj.id in inventory_ids:
            return

        inventory_ids.add(obj.id)

        for tag in obj.tags.all():
            self.inventory_tags.append(tag.name)
