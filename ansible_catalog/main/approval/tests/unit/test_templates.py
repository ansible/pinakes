import pytest

from ansible_catalog.main.tests.factories import TenantFactory
from ansible_catalog.main.approval.tests.factories import TemplateFactory


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
        assert (
            f"UNIQUE constraint failed: {template._meta.app_label}_template.title"
            in str(excinfo.value)
        )

    @pytest.mark.django_db
    def test_empty_template_title(self):
        from django.db import IntegrityError

        tenant = TenantFactory()
        constraint_name = f"{tenant._meta.app_label}_template_title_empty"
        with pytest.raises(IntegrityError) as excinfo:
            TemplateFactory(tenant=tenant, title="")
        assert constraint_name in str(excinfo.value)
