from django.db import migrations, transaction
from automation_services_catalog.main.models import Tenant


def create_template(apps, schema_editor):
    Template = apps.get_model("main", "Template")
    db_alias = schema_editor.connection.alias

    with transaction.atomic():
        tenant = Tenant.current()
        Template.objects.using(db_alias).create(
            title="Built-in Email Notification",
            description="Notify approvers by HTML emails with ebedded links for actions",
            tenant_id=tenant.id,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0029_alter_serviceoffering_name"),
    ]

    operations = [
        migrations.RunPython(create_template),
    ]
