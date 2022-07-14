from django.db import migrations
import pinakes.common.models.fields


def migrate_notification_settings(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    NotificationSetting = apps.get_model("main", "NotificationSetting")

    items = NotificationSetting.objects.using(db_alias).all()
    for item in items:
        item.settings_encrypted = item.settings
    NotificationSetting.objects.bulk_update(items, ["settings_encrypted"])


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0048_source_error_code_source_error_dict_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificationsetting",
            name="settings_encrypted",
            field=pinakes.common.models.fields.EncryptedJsonField(
                help_text="Parameters for configuring the notification method",
                null=True,
            ),
        ),
        migrations.RunPython(
            code=migrate_notification_settings,
        ),
        migrations.RemoveField(
            model_name="notificationsetting",
            name="settings",
        ),
        migrations.RenameField(
            model_name="notificationsetting",
            old_name="settings_encrypted",
            new_name="settings",
        ),
    ]
