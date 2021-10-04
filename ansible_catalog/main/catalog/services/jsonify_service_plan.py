"""JSON the service plan"""

import json

from ansible_catalog.main.catalog.models import CatalogServicePlan


class ServicePlanTemplate:
    """Template for service plans"""

    def __init__(
        self,
        portfolio_item_id,
        service_offering_id,
        create_json_schema,
        id=None,
        name="",
        description="",
        imported=False,
        modified=False,
    ):
        self.portfolio_item_id = portfolio_item_id
        self.service_offering_id = service_offering_id
        self.create_json_schema = create_json_schema
        self.id = id
        self.name = name
        self.description = description
        self.imported = imported
        self.modified = modified


class JsonifyServicePlan:
    """Json catalog service plan"""

    def __init__(self, service_plan, options):
        self.service_plan = service_plan
        self.options = options
        #self.json = {}

    def process(self):
        service_plan_template = ServicePlanTemplate(
            portfolio_item_id=self.service_plan.portfolio_item.id,
            service_offering_id=self.service_plan.portfolio_item.service_offering_ref,
            imported=True,
            modified=True if self.service_plan.modified else False,
            create_json_schema=self._relevant_schema(),
            id=self.service_plan.id,
            name=self.service_plan.name,
            description=self.service_plan.description,
        )
        self.json = service_plan_template.__dict__

        return self

    def _relevant_schema(self):
        schema = self.options.get("schema")

        if schema == "base":
            return self.service_plan.base
        elif schema == "modified":
            return self.service_plan.modified
        else:
            return self.service_plan.modified or self.service_plan.base
