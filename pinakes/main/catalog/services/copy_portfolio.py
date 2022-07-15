"""Copy portfolio service"""
import copy
import logging
from django.db import transaction

from pinakes.main.catalog.models import (
    Portfolio,
    PortfolioItem,
)
from pinakes.main.catalog.services import (
    name,
)
from pinakes.main.catalog.services.copy_image import (
    CopyImage,
)
from pinakes.main.catalog.services.copy_portfolio_item import (
    CopyPortfolioItem,
)


logger = logging.getLogger("catalog")


class CopyPortfolio:
    """Copy portfolio service"""

    def __init__(self, portfolio, options):
        self.portfolio = portfolio
        self.name = options.get("portfolio_name", portfolio.name)

        self.new_portfolio = None

    def process(self):
        """Start copy proces."""
        self.make_copy()

        return self

    @transaction.atomic
    def make_copy(self):
        """Make a copy of the Portfolio."""
        new_icon = (
            CopyImage(self.portfolio.icon).process().new_icon
            if self.portfolio.icon
            else None
        )

        self.new_portfolio = copy.copy(self.portfolio)
        self.new_portfolio.id = None
        self.new_portfolio.keycloak_id = None
        self.new_portfolio.share_count = 0
        self.new_portfolio.name = self._new_portfolio_name()
        self.new_portfolio.icon = new_icon
        self.new_portfolio.save()

        portfolio_items = PortfolioItem.objects.filter(
            portfolio=self.portfolio
        )
        for item in portfolio_items:
            try:
                CopyPortfolioItem(item, self.new_portfolio).process()
            except Exception as error:
                logger.error(
                    "Failed to copy portfolio item %d: %s", item.id, str(error)
                )
                raise

    def _new_portfolio_name(self):
        portfolio_names = [
            portfolio.name for portfolio in Portfolio.objects.all()
        ]

        return (
            name.create_copy_name(self.name, portfolio_names)
            if self.name in portfolio_names
            else self.name
        )
