# Generated by Django 3.2.5 on 2021-11-01 20:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0010_alter_catalogserviceplan_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="catalogserviceplan",
            name="imported",
            field=models.BooleanField(default=True),
        ),
    ]
