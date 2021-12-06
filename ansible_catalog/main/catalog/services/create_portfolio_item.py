"""Create portfolio item service"""
import logging

from ansible_catalog.main.models import Tenant

from ansible_catalog.main.catalog.models import (
    Portfolio,
    PortfolioItem,
)
from ansible_catalog.main.inventory.services.get_service_offering import (
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

        logger.info("Creating portfolio item service options: %s", self.params)

        portfolio_id = self.params.pop("portfolio")
        self.portfolio = Portfolio.objects.get(id=portfolio_id)
        self.service_offering_ref = self.params.get("service_offering_ref")

        svc = GetServiceOffering(self.service_offering_ref).process()
        self.service_offering = svc.service_offering

        self.item = None

    def process(self):
        try:
            self._create_params()

            self.item = PortfolioItem.objects.create(
                tenant=Tenant.current(),
                portfolio=self.portfolio,
                **self.params,
            )
        except Exception as exc:
            logger.error(
                "Service Offering Ref: %s, error: %s",
                self.service_offering_ref,
                str(exc),
            )
            raise

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
        service_offering_columns = [
            field.name for field in self.service_offering._meta.get_fields()
        ]
        portfolio_item_columns = list(
            set([field.name for field in PortfolioItem._meta.get_fields()])
            - set(self.IGNORE_FIELDS)
        )

        return list(
            set(service_offering_columns) & set(portfolio_item_columns)
        )
