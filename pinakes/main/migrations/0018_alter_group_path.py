from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0017_approval_descriptions"),
    ]

    operations = [
        migrations.AlterField(
            model_name="group",
            name="path",
            field=models.TextField(unique=True),
        ),
    ]
