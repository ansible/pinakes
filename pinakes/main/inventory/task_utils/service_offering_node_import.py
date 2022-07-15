"""Import Workflow Job template nodes from Tower"""

import dateutil.parser
from pinakes.main.inventory.models import (
    ServiceOfferingNode,
)


class ServiceOfferingNodeImport:
    "ServiceOfferingNode maps to Workflow Job Template Nodes in Tower"

    # default constructor
    def __init__(self, tenant, source, tower, inventory, service_offerings):
        self.tenant = tenant
        self.source = source
        self.stats = {"adds": 0, "updates": 0, "deletes": 0}
        self.inventory = inventory
        self.tower = tower
        self.old_objects = {}
        self.service_offerings = service_offerings
        self.attrs = (
            "id",
            "summary_fields.unified_job_template.unified_job_type",
            "inventory",
            "type",
            "url",
            "created",
            "modified",
            "workflow_job_template",
            "unified_job_template",
        )

    def get_stats(self):
        """Get the adds/updates/deletes"""
        return self.stats

    def process(self):
        """Start the import process"""
        print("Loading existing objects")
        self._get_old_ids()
        print("Fetching Workflow Job Template Nodes")
        self._process_workflow_job_template_nodes()
        self._deletes()

    def _deletes(self):
        """Delete any left over objects in the old_objects."""
        for key, value in self.old_objects.items():
            print(f"Deleting source_ref {key}, object {value[0]}")
            self.stats["deletes"] += 1
            ServiceOfferingNode.objects.get(pk=value[0]).delete()

    def _handle_obj(self, new_obj):
        """Handle an incoming object from Tower."""
        source_ref = str(new_obj["id"])
        inventory = self._get_inventory(new_obj["inventory"])
        if source_ref in self.old_objects.keys():
            info = self.old_objects[source_ref]
            self._update_db_obj(info, new_obj, inventory)
            del self.old_objects[source_ref]
        else:
            self._create_db_obj(new_obj, source_ref, inventory)

    def _get_inventory(self, value):
        """Get the inventory object id"""
        if value:
            return self.inventory.source_ref_to_id(value)

        return None

    def _process_workflow_job_template_nodes(self):
        """Process workflow Job Template Nodes."""
        for new_obj in self.tower.get(
            "/api/v2/workflow_job_template_nodes?order=id", self.attrs
        ):
            obj_type = new_obj[
                "summary_fields.unified_job_template.unified_job_type"
            ]
            if obj_type in ("job", "workflow_job"):
                self._handle_obj(new_obj)

    def _get_service_offering(self, source_ref):
        """Using the source ref locate the ID of the database object."""
        return self.service_offerings.source_ref_to_id(source_ref)

    def _create_db_obj(self, new_obj, source_ref, inventory):
        """Create a service_offering_node object"""
        self.stats["adds"] += 1
        return ServiceOfferingNode.objects.create(
            source_ref=source_ref,
            tenant=self.tenant,
            source=self.source,
            service_inventory_id=inventory,
            service_offering_id=self._get_service_offering(
                str(new_obj["unified_job_template"])
            ),
            root_service_offering_id=self._get_service_offering(
                str(new_obj["workflow_job_template"])
            ),
            source_created_at=new_obj["created"],
            source_updated_at=new_obj["modified"],
            extra={},
        )

    def _update_db_obj(self, info, new_obj, inventory):
        modified = dateutil.parser.parse(new_obj["modified"])
        if info[1] != modified:
            self.stats["updates"] += 1
            db_obj = ServiceOfferingNode.objects.get(pk=info[0])
            print("Updating modified object")
            db_obj.service_inventory_id = inventory
            db_obj.source_updated_at = modified
            db_obj.save()

    def _get_old_ids(self):
        for info in ServiceOfferingNode.objects.filter(
            tenant=self.tenant, source=self.source
        ).values("id", "source_ref", "source_updated_at"):
            self.old_objects[info["source_ref"]] = (
                info["id"],
                info["source_updated_at"],
            )
        print(self.old_objects)
