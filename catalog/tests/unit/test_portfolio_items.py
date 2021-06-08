import pytest
import pdb

from catalog.tests.factories import PortfolioFactory
from catalog.tests.factories import PortfolioItemFactory
from catalog.tests.factories import TenantFactory


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

        assert "CHECK constraint failed: catalog_portfolioitem_name_empty" in str(
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

        assert "UNIQUE constraint failed: catalog_portfolioitem.name" in str(
            excinfo.value
        )
