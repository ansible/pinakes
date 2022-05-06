from django.db import migrations, transaction


def update_default_template(apps, schema_editor):
    Template = apps.get_model("main", "Template")
    db_alias = schema_editor.connection.alias

    with transaction.atomic():
        Template.objects.using(db_alias).filter(
            title="Built-in Email Notification"
        ).update(
            title="Built-in Approval Template",
            description=(
                "No notifications. Approvers need to log in to check and act "
                "on requests"
            ),
        )


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0046_progressmessage_nullable_fields"),
    ]

    operations = [
        migrations.RunPython(update_default_template),
    ]
