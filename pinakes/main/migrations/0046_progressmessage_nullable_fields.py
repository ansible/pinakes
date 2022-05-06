import logging

from django.db import migrations, models
from django.db.models import Q


logger = logging.getLogger("pinakes")


def upgrade_delete_invalid_progressmessages(apps, schema_editor):
    ProgressMessage = apps.get_model("main", "ProgressMessage")
    db_alias = schema_editor.connection.alias
    deleted_count, _ = (
        ProgressMessage.objects.using(db_alias)
        .filter(
            Q(messageable_id__isnull=True) | Q(messageable_type__isnull=True)
        )
        .delete()
    )
    if deleted_count:
        logger.warning(
            f"Deleted {deleted_count} invalid ProgressMessage records."
        )


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0045_source_last_refresh_stats"),
    ]

    operations = [
        migrations.RunPython(
            code=upgrade_delete_invalid_progressmessages,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="progressmessage",
            name="messageable_id",
            field=models.IntegerField(
                editable=False, help_text="ID of the order or order item"
            ),
        ),
        migrations.AlterField(
            model_name="progressmessage",
            name="messageable_type",
            field=models.CharField(
                editable=False,
                help_text=(
                    "Identify order or order item that this message belongs to"
                ),
                max_length=64,
            ),
        ),
    ]
