# Generated by Django 3.2.5 on 2022-05-26 20:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "main",
            "0050_remove_notificationtype_main_notificationtype_n_type_\
unique_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="progressmessage",
            name="message_params",
            field=models.JSONField(
                help_text="Stores message parameters used by localization",
                null=True,
            ),
        ),
    ]
