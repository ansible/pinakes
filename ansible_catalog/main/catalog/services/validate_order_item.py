""" Validate order item by its service plans. """

from django.utils.translation import gettext_lazy as _

from ansible_catalog.main.catalog.exceptions import (
    InvalidSurveyException,
)
from ansible_catalog.main.catalog.models import ServicePlan
from ansible_catalog.main.catalog.services.compare_service_plans import (
    CompareServicePlans,
)


class ValidateOrderItem:
    """Compare service plans"""

    def __init__(self, order_item):
        self.order_item = order_item

    def process(self):
        service_plans = ServicePlan.objects.filter(
            portfolio_item=self.order_item.portfolio_item
        )

        changed_plans = CompareServicePlans.changed_plans(service_plans)

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
                    "The underlying survey on product {} in the portfolio {} has been changed and is no longer valid, please contact an administrator to fix it."
                ).format(
                    portfolio_item_names,
                    portfolio_names,
                )
            )

        return self
