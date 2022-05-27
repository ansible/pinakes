from django.db import migrations


def create_source(apps, schema_editor):
    """create a default source if none exists"""
    Tenant = apps.get_model("main", "Tenant")
    Source = apps.get_model("main", "Source")
    db_alias = schema_editor.connection.alias

    if Source.objects.using(db_alias).count() > 0:
        return

    tenant, _ = Tenant.objects.using(db_alias).get_or_create(
        external_tenant="default"
    )
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
