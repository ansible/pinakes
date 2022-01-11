""" Compare service plans. """

import logging

from ansible_catalog.main.catalog.services.compare_schema import (
    CompareSchema,
)
from ansible_catalog.main.inventory.services.get_service_plan import (
    GetServicePlan,
)

logger = logging.getLogger("catalog")


class CompareServicePlans:
    """Compare service plans"""

    def __init__(self, service_plan):
        self.base_schema = service_plan.base_schema
        self.service_plan_ref = service_plan.inventory_service_plan_ref

    @classmethod
    def is_outdated(cls, plan):
        if plan.outdated:
            return True

        if cls.is_empty_plan(plan):
            return False

        potential = cls(plan)
        inventory_sha256 = potential._inventory_schema_sha256()

        return plan.base_sha256 != inventory_sha256 and plan.modified

    @classmethod
    def any_changed(cls, plans):
        changed = [plan for plan in plans if cls.is_outdated(plan)]

        return len(changed) > 0

    @classmethod
    def changed_plans(cls, plans):
        return [plan for plan in plans if cls.is_outdated(plan)]

    @staticmethod
    def is_empty_plan(plan):
        return CompareSchema.is_empty_schema(plan.base_schema)

    def _inventory_schema_sha256(self):
        plan = GetServicePlan(self.service_plan_ref).process().service_plan

        return plan.schema_sha256 if plan else ""
