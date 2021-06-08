import pytest

from catalog.tests.factories import PortfolioFactory
from catalog.tests.factories import TenantFactory


class TestPortfolios:
    @pytest.mark.django_db
    def test_portfolio(self):
        tenant = TenantFactory()
        portfolio = PortfolioFactory(tenant=tenant)
        assert tenant.id == portfolio.tenant.id

    @pytest.mark.django_db
    def test_duplicate_portfolio_name(self):
        from django.db import IntegrityError

        tenant = TenantFactory()
        name = "fred"
        portfolio = PortfolioFactory(tenant=tenant, name=name)
        with pytest.raises(IntegrityError) as excinfo:
            PortfolioFactory(tenant=tenant, name=name)
        assert "UNIQUE constraint failed: catalog_portfolio.name" in str(excinfo.value)

    @pytest.mark.django_db
    def test_empty_portfolio_name(self):
        from django.db import IntegrityError

        tenant = TenantFactory()
        constraint_name = "catalog_portfolio_name_empty"
        with pytest.raises(IntegrityError) as excinfo:
            PortfolioFactory(tenant=tenant, name="")
        assert constraint_name in str(excinfo.value)
