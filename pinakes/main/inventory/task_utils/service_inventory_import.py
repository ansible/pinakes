"""ServiceInventoryImport module imports the Inventory
    object from Ansible Tower. It handles adds, updates
    and deletes.
"""
import logging
import dateutil.parser
from pinakes.main.inventory.models import ServiceInventory

logger = logging.getLogger("inventory")


class ServiceInventoryImport:
    """ServiceInventoryImport imports the Tower Inventory objects"""

    def __init__(self, tenant, source, tower):
        self.tenant = tenant
        self.source = source
        self.stats = {"adds": 0, "updates": 0, "deletes": 0}
        self.service_inventory_objects = {}
        self.tower = tower

    def source_ref_to_id(self, source_ref):
        """Given a Source Ref, get the ID of the object
        from the local database."""
        source_id = self.service_inventory_objects.get(source_ref, None)
        if source_id is None:
            logger.warning(
                f"Source {source_ref} is not found in service inventory"
            )

        return source_id

    def get_stats(self):
        """Get the stats of the process, the number of adds,
        updates and deletes."""
        return self.stats

    def process(self):
        """Process, the import handle add, update and deletes"""
        old_ids = self._get_old_ids()
        attrs = [
            "id",
            "type",
            "created",
            "name",
            "modified",
            "description",
            "kind",
        ]

        for new_obj in self.tower.get("/api/v2/inventories?order=id", attrs):
            source_ref = str(new_obj["id"])
            if source_ref in old_ids.keys():
                self._update_db_obj(old_ids[source_ref], new_obj)
                self.service_inventory_objects[source_ref] = old_ids[
                    source_ref
                ][0]
                del old_ids[source_ref]
            else:
                db_obj = self._create_db_obj(new_obj)
                self.service_inventory_objects[source_ref] = db_obj.id

        for _, value in old_ids.items():
            self.stats["deletes"] += 1
            ServiceInventory.objects.get(pk=value[0]).delete()

    def _create_db_obj(self, new_obj):
        """Private method to create a new object."""
        self.stats["adds"] += 1
        return ServiceInventory.objects.create(
            name=new_obj["name"],
            description=new_obj["description"],
            source_ref=str(new_obj["id"]),
            tenant=self.tenant,
            source=self.source,
            source_created_at=new_obj["created"],
            source_updated_at=new_obj["modified"],
            extra={},
        )

    def _update_db_obj(self, info, new_obj):
        """Private method to update an existing object."""
        modified = dateutil.parser.parse(new_obj["modified"])
        if info[1] != modified:
            self.stats["updates"] += 1
            db_obj = ServiceInventory.objects.get(pk=info[0])
            print("Updating modified object")
            db_obj.name = new_obj["name"]
            db_obj.description = new_obj["description"]
            db_obj.source_updated_at = modified
            db_obj.save()

    def _get_old_ids(self):
        """Private method to collect existing inventory
        objects for a quick lookup.

        The updates are compared by looking at the modified attribute
        from tower with the source_updated_at in the local db.
        """
        old_ids = {}
        for info in ServiceInventory.objects.filter(
            tenant=self.tenant, source=self.source
        ).values("id", "source_ref", "source_updated_at"):
            old_ids[info["source_ref"]] = (
                info["id"],
                info["source_updated_at"],
            )
            self.service_inventory_objects[info["source_ref"]] = info["id"]
        return old_ids
