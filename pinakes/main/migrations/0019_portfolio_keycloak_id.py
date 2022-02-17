from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0018_alter_group_path"),
    ]

    operations = [
        migrations.AddField(
            model_name="portfolio",
            name="keycloak_id",
            field=models.CharField(max_length=255, null=True),
        ),
    ]
