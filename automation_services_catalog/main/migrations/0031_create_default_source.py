from django.db import migrations, models, transaction
from automation_services_catalog.main.models import Tenant


def create_source(apps, schema_editor):
    """create a default source if none exists"""
    Source = apps.get_model("main", "Source")
    db_alias = schema_editor.connection.alias

    if Source.objects.using(db_alias).count() > 0:
        return

    with transaction.atomic():
        tenant = Tenant.current()
        Source.objects.using(db_alias).create(
            name="Automation Controller",
            tenant_id=tenant.id,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0030_create_email_template"),
    ]

    operations = [
        migrations.RunPython(create_source),
    ]
