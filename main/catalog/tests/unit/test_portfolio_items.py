import pytest

from main.catalog.tests.factories import PortfolioFactory
from main.catalog.tests.factories import PortfolioItemFactory
from main.tests.factories import TenantFactory


class TestPortfolioItems:
    @pytest.mark.django_db
    def test_portfolioitem(self):
        tenant = TenantFactory()
        portfolio = PortfolioFactory(tenant=tenant)
        portfolio_item = PortfolioItemFactory(tenant=tenant, portfolio=portfolio)
        assert tenant.id == portfolio_item.tenant.id

    @pytest.mark.django_db
    def test_empty_portfolioitem_name(self):
        from django.db import IntegrityError

        tenant = TenantFactory()
        portfolio = PortfolioFactory(tenant=tenant)
        with pytest.raises(IntegrityError) as excinfo:
            PortfolioItemFactory(tenant=tenant, portfolio=portfolio, name="")

        assert f"CHECK constraint failed: {portfolio._meta.app_label}_portfolioitem_name_empty" in str(
            excinfo.value
        )

    @pytest.mark.django_db
    def test_duplicate_portfolioitem_name(self):
        from django.db import IntegrityError

        tenant = TenantFactory()
        portfolio = PortfolioFactory(tenant=tenant)
        name = "fred"
        PortfolioItemFactory(tenant=tenant, portfolio=portfolio, name=name)
        with pytest.raises(IntegrityError) as excinfo:
            PortfolioItemFactory(tenant=tenant, portfolio=portfolio, name=name)

        assert f"UNIQUE constraint failed: {portfolio._meta.app_label}_portfolioitem.name" in str(
            excinfo.value
        )
