import pytest

from pinakes.main.catalog.tests.factories import (
    PortfolioFactory,
)
from pinakes.main.catalog.tests.factories import (
    PortfolioItemFactory,
)
from pinakes.main.tests.factories import TenantFactory


class TestPortfolioItems:
    @pytest.mark.django_db
    def test_portfolioitem(self):
        tenant = TenantFactory()
        portfolio = PortfolioFactory(tenant=tenant)
        portfolio_item = PortfolioItemFactory(
            tenant=tenant, portfolio=portfolio
        )
        assert tenant.id == portfolio_item.tenant.id

    @pytest.mark.django_db
    def test_empty_portfolioitem_name(self):
        from django.db import IntegrityError

        tenant = TenantFactory()
        portfolio = PortfolioFactory(tenant=tenant)
        with pytest.raises(IntegrityError) as excinfo:
            PortfolioItemFactory(tenant=tenant, portfolio=portfolio, name="")

        assert (
            f"CHECK constraint failed: {portfolio._meta.app_label}_portfolioitem_name_empty"
            in str(excinfo.value)
        )

    @pytest.mark.django_db
    def test_portfolio_metadata(self, api_request):
        portfolio_item = PortfolioItemFactory()

        assert portfolio_item.metadata["statistics"]["approval_processes"] == 0

        api_request(
            "post",
            "catalog:portfolioitem-tag",
            portfolio_item.id,
            {"name": "test_tag"},
        )

        assert portfolio_item.metadata["statistics"]["approval_processes"] == 1
