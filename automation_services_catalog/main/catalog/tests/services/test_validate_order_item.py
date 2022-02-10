""" Test population json template with input parameters """
import pytest

from automation_services_catalog.main.catalog.exceptions import (
    InvalidSurveyException,
)
from automation_services_catalog.main.catalog.tests.factories import (
    OrderItemFactory,
    PortfolioItemFactory,
    ServicePlanFactory,
)
from automation_services_catalog.main.inventory.tests.factories import (
    ServiceOfferingFactory,
)
from automation_services_catalog.main.catalog.services.validate_order_item import (
    ValidateOrderItem,
)


@pytest.mark.django_db
def test_process_with_valid_order_item():
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )

    ServicePlanFactory(
        portfolio_item=portfolio_item,
        outdated=False,
    )

    order_item = OrderItemFactory(portfolio_item=portfolio_item)

    svc = ValidateOrderItem(order_item)
    svc.process()

    assert svc.order_item == order_item


@pytest.mark.django_db
def test_process_with_outdated_service_plan():
    service_offering = ServiceOfferingFactory(survey_enabled=True)
    portfolio_item = PortfolioItemFactory(
        service_offering_ref=str(service_offering.id)
    )

    ServicePlanFactory(
        portfolio_item=portfolio_item,
        outdated=True,
    )

    order_item = OrderItemFactory(portfolio_item=portfolio_item)

    svc = ValidateOrderItem(order_item)

    with pytest.raises(InvalidSurveyException) as excinfo:
        svc.process()

    assert "The underlying survey on" in str(excinfo.value)
