# Generated by Django 3.2.8 on 2021-12-20 21:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0026_auto_20211215_2027"),
    ]

    operations = [
        migrations.RenameField(
            model_name="serviceplan",
            old_name="outdated_changes",
            new_name="_base_changes",
        ),
        migrations.RemoveField(
            model_name="serviceplan",
            name="outdated",
        ),
    ]
