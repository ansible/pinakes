"""Copy portfolio item service"""
import copy
import logging
import os
import random
import string
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from ansible_catalog.main.catalog.models import (
    CatalogServicePlan,
    Image,
    Portfolio,
    PortfolioItem,
)
from ansible_catalog.main.catalog.services import (
    name,
)
from ansible_catalog.main.inventory.services.get_service_offering import (
    GetServiceOffering,
)

logger = logging.getLogger("catalog")


class CopyPortfolioItem:
    """Copy portfolio item service"""

    def __init__(self, portfolio_item, options):
        self.portfolio_item = portfolio_item
        self.name = options.get("portfolio_item_name", portfolio_item.name)

        portfolio_id = options.get("portfolio_id", None)
        if portfolio_id:
            self.portfolio = Portfolio.objects.get(id=portfolio_id)
        else:
            self.portfolio = self.portfolio_item.portfolio

        self.new_portfolio_item = None

    def process(self):
        self.make_copy()

        return self

    @transaction.atomic
    def make_copy(self):
        if not self._is_orderable():
            raise RuntimeError(
                _("{} is not orderable, and cannot be copied").format(
                    self.portfolio_item.name
                )
            )

        new_image = self._copy_image() if self.portfolio_item.icon else None

        self.new_portfolio_item = copy.copy(self.portfolio_item)
        self.new_portfolio_item.id = None
        self.new_portfolio_item.name = self._new_portfolio_item_name()
        self.new_portfolio_item.icon = new_image
        self.new_portfolio_item.portfolio = self.portfolio
        self.new_portfolio_item.save()

        service_plans = CatalogServicePlan.objects.filter(
            portfolio_item=self.portfolio_item
        )
        for plan in service_plans:
            new_plan = copy.copy(plan)
            new_plan.id = None
            new_plan.portfolio_item = self.new_portfolio_item
            new_plan.save()

    def _is_orderable(self):
        service_offering_ref = self.portfolio_item.service_offering_ref
        if service_offering_ref is None:
            return False

        svc = GetServiceOffering(service_offering_ref, True).process()
        service_offering = svc.service_offering

        if service_offering is None:
            return False

        if len(svc.service_plans) > 0:
            original_schema = svc.service_plans.first().create_json_schema

        service_plans = CatalogServicePlan.objects.filter(
            portfolio_item=self.portfolio_item
        )
        for service_plan in service_plans:
            if service_plan.base_schema is None:
                return True

            if original_schema != service_plan.base_schema:
                return False

        return True

    def _copy_image(self):
        names = os.path.splitext(self.portfolio_item.icon.file.name)
        rad_sfx = "".join(
            random.choices(string.ascii_letters + string.digits, k=6)
        )
        new_name = "{}{}{}".format(names[0], rad_sfx, names[-1])

        with open(self.portfolio_item.icon.file.path, "rb") as icon:
            data = icon.read()

        copied_image = Image()
        copied_image.file.save(new_name, ContentFile(data))
        copied_image.source_ref = self.portfolio_item.icon.source_ref
        copied_image.save()

        return copied_image

    def _new_portfolio_item_name(self):
        portfolio_items = PortfolioItem.objects.filter(
            portfolio=self.portfolio
        )
        portfolio_item_names = [
            portfolio_item.name for portfolio_item in portfolio_items
        ]

        return (
            name.create_copy_name(self.name, portfolio_item_names)
            if self.name in portfolio_item_names
            else self.name
        )
