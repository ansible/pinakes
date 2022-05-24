import pytest

from pinakes.main.tests.factories import TenantFactory
from pinakes.main.approval.tests.factories import (
    TemplateFactory,
)


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
        TemplateFactory(tenant=tenant, title=title)
        with pytest.raises(IntegrityError):
            TemplateFactory(tenant=tenant, title=title)

    @pytest.mark.django_db
    def test_empty_template_title(self):
        from django.db import IntegrityError

        tenant = TenantFactory()
        constraint_name = f"{tenant._meta.app_label}_template_title_empty"
        with pytest.raises(IntegrityError) as excinfo:
            TemplateFactory(tenant=tenant, title="")
        assert constraint_name in str(excinfo.value)
