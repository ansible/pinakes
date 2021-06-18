""" ServiceOfferingImporter module imports job Templates and
    Workflow Job templates from the tower
"""
import re
import dateutil.parser
from inventory.models import ServiceOffering, OfferingKind, ServicePlan


class ServiceOfferingImport:
    """Import Job Template and Workflow Job Template from tower."""

    # default constructor
    def __init__(self, tenant, source, tower, inventory, service_plan_importer):
        self.tenant = tenant
        self.source = source
        self.stats = {"adds": 0, "updates": 0, "deletes": 0}
        self.inventory = inventory
        self.tower = tower
        self.old_objects = {}
        self.survey_objects = []
        self.service_offering_objects = {}
        self.plan_importer = service_plan_importer
        self.attrs = [
            "id",
            "type",
            "url",
            "created",
            "name",
            "modified",
            "description",
            "survey_enabled",
            "related.survey_spec",
            "related.inventory",
        ]

    def source_ref_to_id(self, source_ref):
        """Convert id from tower to id in local database."""
        return self.service_offering_objects[source_ref]

    def get_stats(self):
        """Get the adds/updates/deletes for this object."""
        return self.stats

    def process(self):
        """Start processing."""
        self.__get_old_ids()
        self.__process_job_templates()
        self.__process_workflow_job_templates()
        self.__deletes()
        self.__fetch_survey_specs()

    def __deletes(self):
        """Delete any left over objects in the old_objects."""
        for key, value in self.old_objects.items():
            print(f"Deleting source_ref {key}, object {value[0]}")
            self.stats["deletes"] += 1
            ServiceOffering.objects.get(pk=value[0]).delete()

    def __fetch_survey_specs(self):
        """Fetch the Survey Spec from tower"""
        for info in self.survey_objects:
            print(f"Importing {info[0]}")
            self.plan_importer.process(info[0], info[1], info[2])

    def __handle_obj(self, new_obj, kind):
        """Handle an object based on kind of object job template or workflow"""
        source_ref = str(new_obj["id"])
        inventory = self.__get_inventory(new_obj["related.inventory"])
        if source_ref in self.old_objects.keys():
            info = self.old_objects[source_ref]
            self.__update_db_obj(info, new_obj, source_ref, inventory)
            self.service_offering_objects[source_ref] = info[0]
            del self.old_objects[source_ref]
        else:
            db_obj = self.__create_db_obj(new_obj, source_ref, kind, inventory)
            self.service_offering_objects[source_ref] = db_obj.id

    def __get_inventory(self, url):
        """Get the inventory id for this object."""
        result = re.search(r"\/api\/v2\/inventories\/(\w*)\/", url)
        if result:
            return self.inventory.source_ref_to_id(result.group(1))

        return None

    def __process_job_templates(self):
        """Process Job Templates."""
        for new_obj in self.tower.get("/api/v2/job_templates?order=id", self.attrs):
            self.__handle_obj(new_obj, OfferingKind.JOB_TEMPLATE)

    def __process_workflow_job_templates(self):
        """Process Workflows."""
        for new_obj in self.tower.get(
            "/api/v2/workflow_job_templates?order=id", self.attrs
        ):
            self.__handle_obj(new_obj, OfferingKind.WORKFLOW)

    def __create_db_obj(self, new_obj, source_ref, kind, inventory):
        """Create a new object in the local DB."""
        print(new_obj["url"])
        print(new_obj["survey_enabled"])

        self.stats["adds"] += 1
        obj = ServiceOffering.objects.create(
            name=new_obj["name"],
            description=new_obj["description"],
            source_ref=source_ref,
            tenant=self.tenant,
            source=self.source,
            service_inventory_id=inventory,
            kind=kind,
            survey_enabled=new_obj["survey_enabled"],
            source_created_at=new_obj["created"],
            source_updated_at=new_obj["modified"],
            extra={},
        )
        if new_obj["survey_enabled"] is True:
            self.survey_objects.append(
                (new_obj["related.survey_spec"], obj.id, source_ref)
            )
        return obj

    def __update_db_obj(self, info, new_obj, source_ref, inventory):
        """Updated the local object in our db if the modified is  different."""
        modified = dateutil.parser.parse(new_obj["modified"])
        if info[1] != modified:
            self.stats["updates"] += 1
            db_obj = ServiceOffering.objects.get(pk=info[0])
            if db_obj.survey_enabled is True and new_obj["survey_enabled"] is False:
                ServicePlan.objects.filter(
                    tenant=self.tenant, source=self.source, source_ref=source_ref
                ).first().delete()

            print("Updating modified object")
            db_obj.name = new_obj["name"]
            db_obj.description = new_obj["description"]
            db_obj.source_updated_at = modified
            db_obj.service_inventory_id = inventory
            db_obj.survey_enabled = new_obj["survey_enabled"]
            db_obj.save()
            if new_obj["survey_enabled"] is True:
                self.survey_objects.append(
                    (new_obj["related.survey_spec"], db_obj.id, source_ref)
                )

    def __get_old_ids(self):
        """Get old objects in the database."""
        for info in ServiceOffering.objects.filter(
            tenant=self.tenant, source=self.source
        ).values("id", "source_ref", "source_updated_at"):
            self.old_objects[info["source_ref"]] = (
                info["id"],
                info["source_updated_at"],
            )
            self.service_offering_objects[info["source_ref"]] = info["id"]
