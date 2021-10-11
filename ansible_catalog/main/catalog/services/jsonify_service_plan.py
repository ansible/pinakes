"""JSON the service plan"""

from ansible_catalog.main.catalog.models import CatalogServicePlan


class JsonifyServicePlan:
    """Json catalog service plan"""

    def __init__(self, service_plan, options):
        self.service_plan = service_plan
        self.options = options
        self.json = None

    def process(self):
        catalog_service_plan = CatalogServicePlan(
            name=self.service_plan.name,
            portfolio_item=self.service_plan.portfolio_item,
            service_offering_ref=self.service_plan.portfolio_item.service_offering_ref,
            service_plan_ref=self.service_plan.id,
            imported=True,
            modified=True if self.service_plan.modified_schema else False,
            create_json_schema=self._relevant_schema(),
        )
        self.json = catalog_service_plan

        return self

    def _relevant_schema(self):
        schema = self.options.get("schema")

        if schema == "base":
            return self.service_plan.base_schema
        elif schema == "modified":
            return self.service_plan.modified_schema
        else:
            return (
                self.service_plan.modified_schema
                or self.service_plan.base_schema
            )
