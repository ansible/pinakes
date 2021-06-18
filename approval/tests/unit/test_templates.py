import pytest

from approval.tests.factories import TemplateFactory
from approval.tests.factories import TenantFactory


class TestTemplate:
    @pytest.mark.django_db
    def test_template(self):
        tenant = TenantFactory()
        template = TemplateFactory(tenant=tenant)
        assert tenant.id == template.tenant.id

    @pytest.mark.django_db
    def test_duplicate_template_title(self):
        from django.db import IntegrityError

        tenant = TenantFactory()
        title = "fred"
        template = TemplateFactory(tenant=tenant, title=title)
        with pytest.raises(IntegrityError) as excinfo:
            TemplateFactory(tenant=tenant, title=title)
        assert "UNIQUE constraint failed: approval_template.title" in str(excinfo.value)

    @pytest.mark.django_db
    def test_empty_template_title(self):
        from django.db import IntegrityError

        tenant = TenantFactory()
        constraint_name = "approval_template_title_empty"
        with pytest.raises(IntegrityError) as excinfo:
            TemplateFactory(tenant=tenant, title="")
        assert constraint_name in str(excinfo.value)
