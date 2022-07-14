from django.db import migrations


def create_template(apps, schema_editor):
    Tenant = apps.get_model("main", "Tenant")
    Template = apps.get_model("main", "Template")
    db_alias = schema_editor.connection.alias

    tenant, _ = Tenant.objects.using(db_alias).get_or_create(
        external_tenant="default"
    )
    Template.objects.using(db_alias).create(
        title="Built-in Email Notification",
        description=(
            "Notify approvers by HTML emails with ebedded links for actions"
        ),
        tenant_id=tenant.id,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0029_alter_serviceoffering_name"),
    ]

    operations = [
        migrations.RunPython(create_template),
    ]
