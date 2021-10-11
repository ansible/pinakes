"""Reset the service plan"""

from ansible_catalog.main.catalog.models import CatalogServicePlan
from ansible_catalog.main.catalog.services.import_service_plan import (
    ImportServicePlan,
)


class ResetServicePlan:
    """Reset catalog service plan"""

    OK_STATUS = "OK"
    NO_CONTENT_STATUS = "NO_CONTENT"

    def __init__(self, service_plan):
        self.service_plan = service_plan
        self.status = self.NO_CONTENT_STATUS
        self.reimported_service_plan = None

    def process(self):
        self.status = (
            self.NO_CONTENT_STATUS
            if self.service_plan.modified_schema
            else self.OK_STATUS
        )
        svc = ImportServicePlan(
            portfolio_item=self.service_plan.portfolio_item,
            force_reset=True,
        ).process()

        self.reimported_service_plan = svc.reimported_service_plan

        return self
