"""Test catalog tasks to add/remove permissions"""
from unittest import mock
import pytest
from django.core.exceptions import ObjectDoesNotExist
from pinakes.main.catalog.models import (
    Portfolio,
)
from pinakes.main.catalog.tests.factories import (
    PortfolioFactory,
)
from pinakes.main.tests.factories import (
    TenantFactory,
    UserFactory,
)
from pinakes.main.catalog.tasks import (
    add_portfolio_permissions,
    remove_portfolio_permissions,
)

from pinakes.main.common.tests.factories import (
    GroupFactory,
)

from pinakes.common.auth.keycloak.models import (
    UmaPermission,
)
from pinakes.common.auth.keycloak_django.utils import (
    make_permission_name,
    make_scope,
)


@pytest.mark.django_db
def test_add_portfolio_permissions(mocker):
    """Test adding portfolio permissions"""
    tenant = TenantFactory()
    user = UserFactory(first_name="John", last_name="Doe")
    portfolio = PortfolioFactory(tenant=tenant, user=user, keycloak_id="abc")
    group = GroupFactory()
    group_ids = [group.id]

    client_mock = mock.Mock()
    mocker.patch(
        "pinakes.common.auth.keycloak_django.get_uma_client",
        return_value=client_mock,
    )
    permission = UmaPermission(
        name=make_permission_name(portfolio, group),
        groups=[group.path],
        scopes=[
            make_scope(portfolio, Portfolio.KEYCLOAK_ACTIONS[0]),
            make_scope(portfolio, Portfolio.KEYCLOAK_ACTIONS[1]),
        ],
    )
    client_mock.find_permissions_by_resource.return_value = [permission]

    mocker.patch(
        "pinakes.main.catalog.tasks.add_group_permissions"
    )
    add_portfolio_permissions(portfolio.id, group_ids, ["read"])
    portfolio.refresh_from_db()
    assert portfolio.share_count == 1


@pytest.mark.django_db
def test_remove_portfolio_permissions(mocker):
    """Test removing portfolio permissions"""
    tenant = TenantFactory()
    user = UserFactory(first_name="John", last_name="Doe")
    portfolio = PortfolioFactory(
        tenant=tenant, user=user, share_count=10, keycloak_id="abc"
    )

    client_mock = mock.Mock()
    mocker.patch(
        "pinakes.common.auth.keycloak_django.get_uma_client",
        return_value=client_mock,
    )
    client_mock.find_permissions_by_resource.return_value = []
    mocker.patch(
        "pinakes.main.catalog.tasks.remove_group_permissions"
    )
    remove_portfolio_permissions(portfolio.id, ["1"], ["read"])
    portfolio.refresh_from_db()
    assert portfolio.share_count == 0


@pytest.mark.django_db
def test_remove_missing_portfolio_permissions(mocker):
    """Test removing portfolio permissions from a missing portfolio"""
    group_ids = ["1", "2", "3"]

    mocker.patch(
        "pinakes.main.catalog.tasks.remove_group_permissions"
    )
    with pytest.raises(ObjectDoesNotExist):
        remove_portfolio_permissions(999999, group_ids, ["read"])
