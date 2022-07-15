"""Validate order item by its service plans."""

from django.utils.translation import gettext_lazy as _

from pinakes.main.catalog.exceptions import (
    InvalidSurveyException,
)
from pinakes.main.catalog.models import ServicePlan


class ValidateOrderItem:
    """Compare service plans"""

    def __init__(self, order_item):
        self.order_item = order_item

    def process(self):
        service_plans = ServicePlan.objects.filter(
            portfolio_item=self.order_item.portfolio_item
        )

        changed_plans = [plan for plan in service_plans if plan.outdated]

        if len(changed_plans) > 0:
            portfolio_item_names = ", ".join(
                list(
                    dict.fromkeys(
                        [plan.portfolio_item.name for plan in changed_plans]
                    )
                )
            )
            portfolio_names = ", ".join(
                list(
                    dict.fromkeys(
                        [
                            plan.portfolio_item.portfolio.name
                            for plan in changed_plans
                        ]
                    )
                )
            )

            raise InvalidSurveyException(
                _(
                    "The underlying survey on product {} in the portfolio {}"
                    " has been changed and is no longer valid, please contact"
                    " an administrator to reset it."
                ).format(
                    portfolio_item_names,
                    portfolio_names,
                )
            )

        return self
