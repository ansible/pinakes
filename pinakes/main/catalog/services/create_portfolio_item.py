"""Create portfolio item service"""
import logging
from django.db import transaction

from pinakes.main.catalog.models import (
    Portfolio,
    PortfolioItem,
    ServicePlan,
)
from pinakes.main.catalog.services.refresh_service_plan import (
    RefreshServicePlan,
)
from pinakes.main.inventory.services.get_service_offering import (
    GetServiceOffering,
)

logger = logging.getLogger("catalog")


class CreatePortfolioItem:
    """Create portfolio item service"""

    IGNORE_FIELDS = [
        "id",
        "created_at",
        "updated_at",
        "portfolio",
        "tenant",
    ]

    def __init__(self, options):
        self.params = options

        self.item = None
        self.service_plan = None

    @transaction.atomic
    def process(self):
        logger.info("Creating portfolio item with options: %s", self.params)

        service_offering_ref = self.params.get("service_offering_ref")
        try:
            logger.info(
                "Fetching service offering from inventory: %s",
                service_offering_ref,
            )
            self.service_offering = (
                GetServiceOffering(service_offering_ref)
                .process()
                .service_offering
            )
        except Exception as error:
            logger.error("Error fetching service offering: %s", str(error))
            raise

        portfolio_id = self.params.pop("portfolio")
        portfolio = Portfolio.objects.get(id=portfolio_id)

        self._create_params()
        self.item = PortfolioItem.objects.create(
            tenant=portfolio.tenant,
            portfolio=portfolio,
            **self.params,
        )

        self.service_plan = ServicePlan.objects.create(
            tenant=portfolio.tenant,
            service_offering_ref=service_offering_ref,
            portfolio_item=self.item,
        )
        RefreshServicePlan(self.service_plan).process()

        return self

    def _create_params(self):
        for field in self._create_fields():
            self.params[field] = self.params.get(field, None) or getattr(
                self.service_offering, field
            )

        self.params["service_offering_source_ref"] = str(
            self.service_offering.source_id
        )

    def _create_fields(self):
        service_offering_columns = {
            field.name for field in self.service_offering._meta.get_fields()
        }
        portfolio_item_columns = {
            field.name for field in PortfolioItem._meta.get_fields()
        } - set(self.IGNORE_FIELDS)

        return list(service_offering_columns & portfolio_item_columns)
