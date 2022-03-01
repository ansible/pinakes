"""Test copy portfolio service"""
from unittest.mock import patch
import pytest

from pinakes.main.models import (
    Image,
)
from pinakes.main.catalog.models import (
    Portfolio,
    PortfolioItem,
)
from pinakes.main.catalog.services.copy_portfolio import (
    CopyPortfolio,
)
from pinakes.main.catalog.tests.factories import (
    ImageFactory,
    PortfolioFactory,
    PortfolioItemFactory,
)


@pytest.mark.django_db
def test_portfolio_copy():
    """Copy a portfolio without portfolio items."""
    portfolio = PortfolioFactory(share_count=10, keycloak_id="gobbledegook")
    options = {
        "portfolio_name": "my test",
    }

    svc = CopyPortfolio(portfolio, options)
    svc.process()

    assert Portfolio.objects.count() == 2
    assert svc.new_portfolio.name == "my test"
    assert svc.new_portfolio.keycloak_id is None
    assert svc.new_portfolio.share_count == 0


@pytest.mark.django_db
def test_portfolio_copy_with_portfolio_items():
    """Copy a portfolio with portfolio items."""
    portfolio = PortfolioFactory()
    PortfolioItemFactory(portfolio=portfolio)

    with patch(
        "pinakes.main.catalog.services.copy_portfolio_item.CopyPortfolioItem._is_orderable"
    ) as mock:
        mock.return_value = True
        svc = CopyPortfolio(portfolio, {})
        svc.process()

    assert Portfolio.objects.count() == 2
    assert PortfolioItem.objects.count() == 2
    assert PortfolioItem.objects.first().portfolio == portfolio
    assert PortfolioItem.objects.last().portfolio == svc.new_portfolio
    assert svc.new_portfolio.name == f"Copy of {portfolio.name}"
    assert (
        PortfolioItem.objects.first().name == PortfolioItem.objects.last().name
    )


@pytest.mark.django_db
def test_portfolio_copy_with_icon():
    """Copy a portfolio with icon."""
    image = ImageFactory()
    portfolio = PortfolioFactory(icon=image)

    assert Image.objects.count() == 1

    svc = CopyPortfolio(portfolio, {})
    svc.process()

    assert Portfolio.objects.count() == 2
    assert Image.objects.count() == 2
    assert Portfolio.objects.first().icon == Image.objects.first()
    assert Portfolio.objects.last().icon == Image.objects.last()
    new_portfolio = svc.new_portfolio
    new_portfolio.delete()
