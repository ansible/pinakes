import pytest

from approval.tests.factories import TenantFactory


class TestTenants:
    @pytest.mark.django_db
    def test_tenant(self):
        tenant = TenantFactory()
        assert tenant.external_tenant.startswith("external")
