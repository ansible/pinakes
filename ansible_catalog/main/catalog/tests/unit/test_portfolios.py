import pytest

from ansible_catalog.main.catalog.tests.factories import (
    PortfolioFactory,
    PortfolioItemFactory,
)
from ansible_catalog.main.tests.factories import TenantFactory, UserFactory


class TestPortfolios:
    @pytest.mark.django_db
    def test_portfolio(self):
        tenant = TenantFactory()
        user = UserFactory(first_name="John", last_name="Doe")

        portfolio = PortfolioFactory(tenant=tenant, user=user)
        assert tenant.id == portfolio.tenant.id
        assert portfolio.owner == f"{user.first_name} {user.last_name}"

    @pytest.mark.django_db
    def test_duplicate_portfolio_name(self):
        from django.db import IntegrityError

        tenant = TenantFactory()
        name = "fred"
        portfolio = PortfolioFactory(tenant=tenant, name=name)
        with pytest.raises(IntegrityError) as excinfo:
            PortfolioFactory(tenant=tenant, name=name)
        assert (
            f"UNIQUE constraint failed: {portfolio._meta.app_label}_portfolio.name"
            in str(excinfo.value)
        )

    @pytest.mark.django_db
    def test_empty_portfolio_name(self):
        from django.db import IntegrityError

        tenant = TenantFactory()
        constraint_name = f"{tenant._meta.app_label}_portfolio_name_empty"
        with pytest.raises(IntegrityError) as excinfo:
            PortfolioFactory(tenant=tenant, name="")
        assert constraint_name in str(excinfo.value)

    @pytest.mark.django_db
    def test_portfolio_metadata(self, api_request):
        portfolio = PortfolioFactory()

        assert portfolio.metadata["statistics"]["approval_processes"] == 0
        assert portfolio.metadata["statistics"]["portfolio_items"] == 0

        PortfolioItemFactory(portfolio=portfolio)
        api_request(
            "post", "portfolio-tag", portfolio.id, {"name": "test_tag"}
        )

        assert portfolio.metadata["statistics"]["portfolio_items"] == 1
        assert portfolio.metadata["statistics"]["approval_processes"] == 1
