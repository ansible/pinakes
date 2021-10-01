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

    def __init__(self, options):
        self.options = options
        self.service_plans = self._get_service_plans()
        self.json = []

    def process(self):
        for service_plan in self._relevant_service_plans():
            service_plan_template = ServicePlanTemplate(
                portfolio_item_id=service_plan.portfolio_item.id,
                service_offering_id=service_plan.portfolio_item.service_offering_ref,
                imported=True,
                modified=True if service_plan.modified else False,
                create_json_schema=self._relevant_schema(service_plan),
                id=service_plan.id,
                name=service_plan.name,
                description=service_plan.description,
            )
            self.json.append(service_plan_template.__dict__)

        return self

    def _relevant_service_plans(self):
        if self.options.get("collection", None) is None:
            return self.service_plans
        else:
            return [self.service_plans.first()]

    def _relevant_schema(self, plan):
        schema = self.options.get("schema")

        if schema == "base":
            return plan.base
        elif schema == "modified":
            return plan.modified
        else:
            return plan.modified or plan.base

    def _get_service_plans(self):
        service_plan_id = self.options.get("service_plan_id", None)
        if service_plan_id is not None:
            return CatalogServicePlan.objects.filter(id=int(service_plan_id))

        portfolio_item_id = self.options.get("portfolio_item_id", None)
        if portfolio_item_id is not None:
            return CatalogServicePlan.objects.filter(
                portfolio_item_id=portfolio_item_id
            )

        return self.options.get("service_plans")
        # service_plans = self.options.get("service_plans", None)
        # if service_plans:
        #     return service_plans
        # else:
        #     raise RuntimeError("Service Plans not found")
