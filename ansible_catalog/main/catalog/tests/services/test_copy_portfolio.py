"""Test copy portfolio service"""
from unittest.mock import patch
import pytest

from ansible_catalog.main.models import (
    Image,
)
from ansible_catalog.main.catalog.models import (
    Portfolio,
    PortfolioItem,
)
from ansible_catalog.main.catalog.services.copy_portfolio import (
    CopyPortfolio,
)
from ansible_catalog.main.catalog.tests.factories import (
    ImageFactory,
    PortfolioFactory,
    PortfolioItemFactory,
)


@pytest.mark.django_db
def test_portfolio_copy():
    portfolio = PortfolioFactory()
    options = {
        "portfolio_name": "my test",
    }

    svc = CopyPortfolio(portfolio, options)
    svc.process()

    assert Portfolio.objects.count() == 2
    assert svc.new_portfolio.name == "my test"


@pytest.mark.django_db
def test_portfolio_copy_with_portfolio_items():
    portfolio = PortfolioFactory()
    PortfolioItemFactory(portfolio=portfolio)

    with patch(
        "ansible_catalog.main.catalog.services.copy_portfolio_item.CopyPortfolioItem._is_orderable"
    ) as mock:
        mock.return_value = True
        svc = CopyPortfolio(portfolio, {})
        svc.process()

    assert Portfolio.objects.count() == 2
    assert PortfolioItem.objects.count() == 2
    assert svc.new_portfolio.name == "Copy of %s" % portfolio.name
    assert (
        PortfolioItem.objects.last().name
        == "Copy of %s" % PortfolioItem.objects.first().name
    )


@pytest.mark.django_db
def test_portfolio_copy_with_icon():
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
