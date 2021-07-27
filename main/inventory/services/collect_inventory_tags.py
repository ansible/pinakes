""" Collect Inventory Tags for a given service offering """
from django.utils.translation import gettext_lazy as _
from main.inventory.models import (
    ServiceOffering,
    ServiceOfferingNode,
    OfferingKind,
    ServiceInventory,
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
        self.__collect_inventory(self.service_offering_id, visited, inventory_ids)
        for object_id in inventory_ids:
            for obj in ServiceInventory.objects.filter(id=object_id):
                for tag in obj.tags.all():
                    self.inventory_tags.append(tag.name)

    def tags(self):
        """Return the list of tags assigned to the given service_offering"""
        return self.inventory_tags

    def __collect_inventory(self, object_id, visited, inventory_ids):
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
            inventory_ids.add(obj.service_inventory.id)

        if obj.kind == OfferingKind.WORKFLOW:
            self.__process_children(obj.id, visited, inventory_ids)

    def __process_children(self, root_id, visited, inventory_ids):
        """Collect Inventory objects for children"""
        for son in ServiceOfferingNode.objects.filter(root_service_offering_id=root_id):
            if son.service_inventory is not None:
                inventory_ids.add(son.service_inventory_id)
            self.__collect_inventory(son.service_offering_id, visited, inventory_ids)
