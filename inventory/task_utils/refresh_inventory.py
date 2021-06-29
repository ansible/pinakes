""" Task to Refresh Inventory from the Tower """
from inventory.basemodel import Source, Tenant
from inventory.task_utils.service_inventory_import import ServiceInventoryImport
from inventory.task_utils.service_offering_import import ServiceOfferingImport
from inventory.task_utils.service_plan_import import ServicePlanImport
from inventory.task_utils.service_offering_node_import import ServiceOfferingNodeImport
from inventory.task_utils.tower_api import TowerAPI
from inventory.task_utils.spec_to_ddf import SpecToDDF


class RefreshInventory:
    """RefreshInventory imports objects from the tower"""

    # default constructor
    def __init__(self, tenant_id, source_id):
        self.tower = TowerAPI()
        self.source = Source.objects.get(pk=source_id)
        self.tenant = Tenant.objects.get(pk=tenant_id)

    # start processing
    def process(self):
        """Run the import process"""
        spec_converter = SpecToDDF()
        plan_importer = ServicePlanImport(
            self.tenant, self.source, self.tower, spec_converter
        )
        sii = ServiceInventoryImport(self.tenant, self.source, self.tower)
        print("Fetching Inventory")
        sii.process()
        soi = ServiceOfferingImport(
            self.tenant, self.source, self.tower, sii, plan_importer
        )
        print("Fetching Job Templates & Workflows")
        soi.process()
        son = ServiceOfferingNodeImport(self.tenant, self.source, self.tower, sii, soi)
        print("Fetching Workflow Template Nodes")
        son.process()
