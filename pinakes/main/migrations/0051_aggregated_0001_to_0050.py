# flake8: noqa
# fmt: off
import base64
import os

from django.conf import settings
from django.db import migrations, models
from django.db.models.fields.files import ImageFieldFile, FileField
import taggit.managers

from pinakes.main.catalog.models import MessageableMixin
from pinakes.common.models.fields import EncryptedJsonField
from pinakes.common.auth.keycloak_django.models import KeycloakMixin


def default_tenant(apps, db_alias):
    Tenant = apps.get_model("main", "Tenant")
    tenant, _ = Tenant.objects.using(db_alias).get_or_create(
        external_tenant="default"
    )
    return tenant


# pinakes.main.migrations.0030_create_email_template
def create_template(apps, schema_editor):
    Template = apps.get_model("main", "Template")
    db_alias = schema_editor.connection.alias

    tenant = default_tenant(apps, db_alias)
    Template.objects.using(db_alias).create(
        title="Built-in Approval Template",
        description=(
            "No notifications. Approvers need to log in to check and act "
            "on requests"
        ),
        tenant_id=tenant.id,
    )


# pinakes.main.migrations.0031_create_default_source
def create_source(apps, schema_editor):
    Source = apps.get_model("main", "Source")
    db_alias = schema_editor.connection.alias

    if Source.objects.using(db_alias).count() > 0:
        return

    tenant = default_tenant(apps, db_alias)
    Source.objects.using(db_alias).create(
        name="Automation Controller",
        tenant_id=tenant.id,
    )


NOTIFICATION_TYPE_SCHEMA = {
    "schemaType": "default",
    "schema": {
        "fields": [
            {
                "label": "Host",
                "name": "host",
                "helper_text": "The SMTP host to use for sending email",
                "isRequired": True,
                "component": "text-field",
                "type": "string",
                "validate": [
                    {"type": "required-validator"},
                ],
            },
            {
                "label": "Port",
                "name": "port",
                "initialValue": 25,
                "helper_text": "Port to use for the SMPT server",
                "component": "text-field",
                "type": "string",
                "dataType": "integer",
                "validate": [
                    {"type": "required-validator"},
                    {"type": "min-number-value", "value": 1},
                ],
            },
            {
                "label": "Username",
                "name": "username",
                "helper_text": "Username to authenticate with the SMTP server",
                "isRequired": False,
                "component": "text-field",
                "type": "string",
            },
            {
                "label": "Password",
                "name": "password",
                "helper_text": "Password to authenticate with the SMTP server",
                "isRequired": False,
                "component": "text-field",
                "type": "password",
            },
            {
                "label": "Security",
                "name": "security",
                "helper_text": "Choose a security connection method to SMTP",
                "component": "select-field",
                "isRequired": False,
                "options": [
                    {"label": "SSL", "value": "use_ssl"},
                    {"label": "TLS", "value": "use_tls"},
                ],
            },
            {
                "label": "SSL Key",
                "name": "ssl_key",
                "helper_text": (
                    "PEM-formatted private key to use for the SSL connection"
                ),
                "isRequired": False,
                "component": "textarea",
                "type": "string",
            },
            {
                "label": "SSL Certificate",
                "name": "ssl_cert",
                "helper_text": (
                    "PEM-formatted certificate chain to use for the SSL "
                    "connection"
                ),
                "isRequired": False,
                "component": "textarea",
                "type": "string",
            },
            {
                "label": "From",
                "name": "from",
                "helper_text": "Sender's email address",
                "isRequired": True,
                "component": "text-field",
                "type": "string",
            },
        ],
        "title": "SMTP Configuration",
        "description": "Settings for sending emails",
    },
}


EMAIL_ICON = b"""
    iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAABmJLR0QA/wD/AP+gvaeTAAAFK
    klEQVR4nO3ZeYxeUxjH8c90tKNFa1r+IWqp/Q9EaKhgpCHW2sKoLZYgaUgJCSJNW0SEShRNJbZY
    E1sQS2U0sTSI+sMegiD2tBpLNa0q44/nvJ39fe99t2nrfv+Zee8957nP+Z1znue551JQUFBQUFB
    QUFDwv6Ql/Z2A+7DFMPrSTFbhQqwoCdCBV9P/n+Pb4fCqCUzE7un/I/Ba6UYHurEGK3B4011rPB
    1ibGvEWDtgRL9G5+NrdOHcZnrXYDqxCN/josEalFZAB7bEC/gXs/XEiUbQilENtN+CuWIsz4ux9
    R7revpfbMVd6dpDdXZyFyzEN8mxbizHkzikjs9pwyPJ/h1iTGQUoMTl+EcEi/F1cGoaVosgexPO
    wXRch4+EINfW4TkT8AbWYWa/e7kEgBPxJz7DpBqc2kOkn+cwBnvhPCHCDiIeLRAiHFfDc3YTmex
    PIXh/cgsAB+BHLMPBVTr2sFjq43CZnuXfjb9wFkbiS7xd5TMOxS/4AfsP0aYqAWBHsUxX4/Scjr
    ViJe5Ov08QS30Kzk42v073bhTbrj3nM84UKe4DsaKGomoBiNnrErN3TQ7ndk/2r+h1rRV7i1n7J
    N2HM9L/+2a03YJZyadF2KpC+5oEIJbpPan9Pel3JSan9tPT79PEdlqJt8T2KgkwTXYBRuHB1H4h
    NsvQp2YBSlwtVO8SK6MceyX7M4Rgq/AHtk33n9YjwMXJ7oQKNttF+f4Prszhd90EIGZytYgNO5Z
    pN0bsz9vELK1K/Q7GBXrK00l4CksqPHcSPk12Ts7pc10FIAaxDD+JbDEUL4rip01kgdKg38VU/C
    by9q84qIydKb2ed2AV/tZdAKK6+1Tk3pOGaHMQ/sb9Yu+OFW9npVK7XQxu6zLP6ZRtxZWjIQLQd
    09eMUSbC4UIX+F2EUduEXn/kgr2r5U95pSjYQLQNyrfpaf+7s0+YhV8Jt7OlohafagZHSkOa/Jk
    nXI0VABiSd+d7L0g3sCqZWssTraur9019Btr//OAejBRVHo/ieC2BNtXYWdnvClixxpxSDO6Tj6
    up94CbIOXRaSfKo6dtsNSQ9fmgzFZxIXxYqY6RYB8QrZiJzf12AJjxIytEs6WKGWIlWJlVOKUZO
    NjfePCuSIIPqy2iWtIDBiJl7AWxwxyf7w4U1iHS8vYmSmyyGKDR/prkp93VuknDRCgBQ+I2Tm/T
    Ls2MXvdmK/vLLaKs4BukSHKRfpbU7urq/CVBggwL/W9KkPbFsxJ7Z8R26b3GeScjDbuTe0HPeCs
    QF0FuDL1m5ez3wViuyzVc8bQmaP/ZuJkaZ1hfBc4U+zXR1UXlKaKun8FDqui/2i8Lk6TjsrRry4
    CHC1mcJHaKrNt5D/56c04vIffZU+zNQtwoEhpS9VW5dWLbUVZvRx7ZmhfUyW4qwhYP+N48fY33C
    zHkSKOdIlKNDN5BNgOr4jAc6R4J99Q+A7Hiq/bL8nxDSOrAGPFgUa7OLP/JqeDzeBjIcJOIjZl2
    p5ZBNhcfFfbU5Sy71fpYDN4R6TF/USd0Za141BBsFWc0a3DqfXxsSmUUvRjBk5yrixwR7pern7f
    UJkhfF/Q73pmAeama7Ma52PDucHAMWQS4BI9Hxs2duaLsZS+ElcUYJrY888a/ExvY2MEHhcxoVM
    FAWaLguJVEf03FUaJ1LgWNysjwL+ith7bZAebwZYiTZY+yXcw8Hyt9JHi6eb51VQGbOmSAF/gQ6
    HSWJvmCijxlXiH+WK4HSkoKCgoKCgoKCgYRv4DQKxzXWNWTxQAAAAASUVORK5CYII=
    """


# pinakes.main.migrations.0040_seed_email_notification_type
def create_notification_type(apps, schema_editor):
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    icon_path = os.path.join(settings.MEDIA_ROOT, "email-icon.png")
    if not os.path.exists(icon_path):
        icon_string = EMAIL_ICON.replace(b"\n", b"").replace(b"    ", b"")
        icon_binary = base64.b64decode(icon_string)
        with open(icon_path, "wb") as file:
            file.write(icon_binary)

    icon_file = ImageFieldFile(
        instance=None, field=FileField(), name="email-icon.png"
    )

    NotificationType = apps.get_model("main", "NotificationType")
    Image = apps.get_model("main", "Image")
    db_alias = schema_editor.connection.alias

    NotificationType.objects.using(db_alias).create(
        n_type="email",
        setting_schema=NOTIFICATION_TYPE_SCHEMA,
        icon=Image.objects.using(db_alias).create(file=icon_file),
    )


def upgrade(apps, schema_editor):
    create_template(apps, schema_editor)
    create_source(apps, schema_editor)
    create_notification_type(apps, schema_editor)


class Migration(migrations.Migration):

    replaces = [
        ("main", "0001_initial"),
        ("main", "0002_auto_20210805_1656"),
        ("main", "0003_auto_20210805_1949"),
        ("main", "0004_auto_20210818_1530"),
        ("main", "0005_auto_20210827_1556"),
        ("main", "0006_auto_20210903_1437"),
        ("main", "0007_auto_20210914_2122"),
        ("main", "0008_alter_request_parent"),
        ("main", "0009_auto_20211004_2054"),
        ("main", "0010_alter_catalogserviceplan_name"),
        ("main", "0011_alter_catalogserviceplan_imported"),
        ("main", "0012_auto_20211102_2131"),
        ("main", "0013_auto_20211108_1729"),
        ("main", "0014_remove_portfolioitem_main_portfolioitem_name_unique"),
        ("main", "0015_group"),
        ("main", "0016_alter_approvalrequest_state"),
        ("main", "0017_approval_descriptions"),
        ("main", "0018_alter_group_path"),
        ("main", "0019_portfolio_keycloak_id"),
        ("main", "0020_auto_20211208_2019"),
        ("main", "0021_auto_20211214_1529"),
        ("main", "0022_auto_20211214_1835"),
        ("main", "0023_inventoryserviceplan_schema_sha256"),
        ("main", "0024_auto_20211215_1927"),
        ("main", "0025_auto_20211215_1928"),
        ("main", "0026_auto_20211215_2027"),
        ("main", "0027_auto_20220114_1950"),
        ("main", "0028_request_keycloak_id"),
        ("main", "0029_alter_serviceoffering_name"),
        ("main", "0030_create_email_template"),
        ("main", "0031_create_default_source"),
        ("main", "0032_auto_20220131_1610"),
        ("main", "0033_auto_20220203_1418"),
        ("main", "0034_source_info"),
        ("main", "0035_source_last_refresh_task_ref"),
        ("main", "0036_portfolio_share_count"),
        ("main", "0037_notification_and_more"),
        ("main", "0038_seed_email_notification"),
        ("main", "0039_remove_template_process_setting_and_more"),
        ("main", "0040_seed_email_notification_type"),
        (
            "main",
            "0041_alter_notificationsetting_settings"
            + "_alter_order_state_and_more",
        ),
        ("main", "0042_alter_order_state_alter_orderitem_state"),
        ("main", "0043_alter_source_refresh_state"),
        ("main", "0044_alter_portfolioitem_name_alter_serviceoffering_name"),
        ("main", "0045_source_last_refresh_stats"),
        ("main", "0046_progressmessage_nullable_fields"),
        ("main", "0047_rename_default_template"),
        ("main", "0048_source_error_code_source_error_dict_and_more"),
        ("main", "0049_notificationsetting_encryption"),
        (
            "main",
            "0050_remove_notificationtype_main_notificationtype"
            + "_n_type_unique_and_more",
        ),
    ]

    initial = True

    dependencies = [
        ("taggit", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.ImageField(blank=True, help_text='The image file', null=True, upload_to='')),
                ('source_ref', models.CharField(default='', max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='InventoryServicePlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the object was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The time at which the object was last updated')),
                ('source_created_at', models.DateTimeField(editable=False, null=True)),
                ('source_updated_at', models.DateTimeField(editable=False, null=True)),
                ('source_ref', models.CharField(max_length=32)),
                ('name', models.CharField(blank=True, max_length=255)),
                ('extra', models.JSONField()),
                ('create_json_schema', models.JSONField()),
                ('update_json_schema', models.JSONField(null=True)),
                ('schema_sha256', models.TextField(blank=True, default='')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NotificationSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the object was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The time at which the object was last updated')),
                ('name', models.CharField(help_text='Name of the notification method', max_length=128)),
                ('settings', EncryptedJsonField(help_text='Parameters for configuring the notification method', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the object was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The time at which the object was last updated')),
                ('state', models.CharField(choices=[('Approval Pending', 'Pending'), ('Approved', 'Approved'), ('Canceled', 'Canceled'), ('Completed', 'Completed'), ('Created', 'Created'), ('Denied', 'Denied'), ('Failed', 'Failed'), ('Ordered', 'Ordered')], default='Created', editable=False, help_text='Current state of the order', max_length=20)),
                ('order_request_sent_at', models.DateTimeField(editable=False, help_text='The time at which the order request was sent to the catalog inventory service', null=True)),
                ('completed_at', models.DateTimeField(editable=False, help_text='The time at which the order completed', null=True)),
            ],
            bases=(
                models.Model,
                MessageableMixin,
                KeycloakMixin
            ),
        ),
        migrations.CreateModel(
            name='Portfolio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the object was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The time at which the object was last updated')),
                ('keycloak_id', models.CharField(max_length=255, null=True)),
                ('name', models.CharField(help_text='Portfolio name', max_length=255)),
                ('description', models.TextField(blank=True, default='', help_text='Describe the portfolio in details')),
                ('enabled', models.BooleanField(default=False, help_text='Whether or not this portfolio is enabled')),
                ('share_count', models.IntegerField(default=0, help_text='The number of different groups sharing this portfolio')),
                ('icon', models.ForeignKey(blank=True, help_text='ID of the icon image associated with this object', null=True, on_delete=models.SET_NULL, to='main.image')),
                ('tags', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags')),
            ],
            bases=(
                KeycloakMixin,
                models.Model
            ),
        ),
        migrations.CreateModel(
            name='PortfolioItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the object was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The time at which the object was last updated')),
                ('favorite', models.BooleanField(default=False, help_text='Definition of a favorite portfolio item')),
                ('description', models.TextField(blank=True, default='', help_text='Description of the portfolio item')),
                ('orphan', models.BooleanField(default=False, help_text='Boolean if an associated service offering no longer exists')),
                ('state', models.CharField(help_text='The current state of the portfolio item', max_length=64)),
                ('service_offering_ref', models.CharField(help_text='The service offering this portfolio item was created from', max_length=64, null=True)),
                ('service_offering_source_ref', models.CharField(blank=True, default='', help_text='The source reference this portfolio item was created from', max_length=64)),
                ('name', models.CharField(help_text='Name of the portfolio item', max_length=512)),
                ('long_description', models.TextField(blank=True, default='', help_text='The longer description of the portfolio item')),
                ('distributor', models.CharField(help_text='The name of the provider for the portfolio item', max_length=64)),
                ('documentation_url', models.URLField(blank=True, help_text='The URL for documentation of the portfolio item')),
                ('support_url', models.URLField(blank=True, help_text='The URL for finding support for the portfolio item')),
                ('icon', models.ForeignKey(blank=True, help_text='ID of the icon image associated with this object', null=True, on_delete=models.SET_NULL, to='main.image')),
                ('portfolio', models.ForeignKey(help_text='ID of the parent portfolio', on_delete=models.CASCADE, to='main.portfolio')),
                ('tags', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags')),
            ],
            bases=(
                KeycloakMixin,
                models.Model
            ),
        ),
        migrations.CreateModel(
            name='RequestContext',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.JSONField()),
                ('context', models.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='ServiceInventory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the object was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The time at which the object was last updated')),
                ('source_created_at', models.DateTimeField(editable=False, null=True)),
                ('source_updated_at', models.DateTimeField(editable=False, null=True)),
                ('source_ref', models.CharField(max_length=32)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('extra', models.JSONField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ServiceOffering',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the object was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The time at which the object was last updated')),
                ('source_created_at', models.DateTimeField(editable=False, null=True)),
                ('source_updated_at', models.DateTimeField(editable=False, null=True)),
                ('source_ref', models.CharField(max_length=32)),
                ('name', models.CharField(max_length=512)),
                ('description', models.TextField(blank=True, default='')),
                ('survey_enabled', models.BooleanField(default=False)),
                ('kind', models.IntegerField(choices=[(0, 'JobTemplate'), (1, 'Workflow')], default=0)),
                ('extra', models.JSONField()),
                ('service_inventory', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to='main.serviceinventory')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Template',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the object was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The time at which the object was last updated')),
                ('title', models.CharField(help_text='Name of the template', max_length=255)),
                ('description', models.TextField(blank=True, default='', help_text='Describe the template with more details')),
                ('process_method', models.ForeignKey(help_text='ID of the notification method for processing the workflow', null=True, on_delete=models.CASCADE, related_name='process_notification', to='main.notificationsetting')),
                ('signal_method', models.ForeignKey(help_text=('ID of the notification method for signaling the completion of the workflow',), null=True, on_delete=models.CASCADE, related_name='signal_notification', to='main.notificationsetting')),
            ],
            bases=(
                KeycloakMixin,
                models.Model
            ),
        ),
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_tenant', models.CharField(help_text="User's account number", max_length=32, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the object was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The time at which the object was last updated')),
            ],
        ),
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the object was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The time at which the object was last updated')),
                ('name', models.CharField(help_text='Name of the workflow', max_length=255)),
                ('description', models.TextField(blank=True, default='', help_text='Describe the workflow in more details')),
                ('group_refs', models.JSONField(default=list, help_text='Array of RBAC groups associated with workflow. The groups need to have approval permission')),
                ('internal_sequence', models.DecimalField(db_index=True, decimal_places=6, max_digits=16)),
                ('template', models.ForeignKey(help_text='ID of the template that the workflow belongs to', on_delete=models.CASCADE, to='main.template')),
                ('tenant', models.ForeignKey(help_text='ID of the tenant the object belongs to', on_delete=models.CASCADE, to='main.tenant')),
            ],
            bases=(
                KeycloakMixin,
                models.Model
            ),
        ),
        migrations.AddField(
            model_name='template',
            name='tenant',
            field=models.ForeignKey(
                help_text='ID of the tenant the object belongs to',
                on_delete=models.CASCADE,
                to='main.tenant'),
        ),
        migrations.CreateModel(
            name='TagLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the object was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The time at which the object was last updated')),
                ('app_name', models.CharField(editable=False, max_length=128)),
                ('tag_name', models.CharField(editable=False, max_length=128)),
                ('object_type', models.CharField(editable=False, max_length=32)),
                ('tenant', models.ForeignKey(help_text='ID of the tenant the object belongs to', on_delete=models.CASCADE, to='main.tenant')),
                ('workflow', models.ForeignKey(null=True, on_delete=models.SET_NULL, to='main.workflow')),
            ],
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of the source', max_length=255, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the object was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The time at which the object was last updated')),
                ('refresh_state', models.CharField(choices=[('Done', 'Done'), ('InProgress', 'In Progress'), ('Failed', 'Failed'), ('Unknown', 'Unknown')], default='Unknown', editable=False, help_text='State of current refresh', max_length=32)),
                ('refresh_started_at', models.DateTimeField(editable=False, help_text='The time at which the source refresh is started', null=True)),
                ('refresh_finished_at', models.DateTimeField(editable=False, help_text='The time at which the source refresh is finished', null=True)),
                ('last_successful_refresh_at', models.DateTimeField(editable=False, help_text='The time at which the latest source refresh was succeeded', null=True)),
                ('last_refresh_message', models.TextField(blank=True, default='', help_text='The message for the last source refresh')),
                ('last_refresh_task_ref', models.CharField(help_text='The last refresh task id', max_length=64, null=True)),
                ('last_refresh_stats', models.JSONField(blank=True, default=dict, help_text='The result stats for the last source refresh')),
                ('availability_status', models.TextField(blank=True, default='unavailable', help_text='The status for the source availability status')),
                ('last_available_at', models.DateTimeField(editable=False, help_text='The time at which the source was available', null=True)),
                ('last_checked_at', models.DateTimeField(editable=False, help_text='The time at which the source was checked availability', null=True)),
                ('availability_message', models.TextField(blank=True, default='Unavailable', help_text='The message about the source availability')),
                ('info', models.JSONField(blank=True, help_text='The information about the source', null=True)),
                ('error_code', models.IntegerField(choices=[(0, 'Success'), (1, 'Failed'), (2, 'Bounded Source')], default=0)),
                ('error_dict', models.JSONField(blank=True, default=dict, help_text='Stores error args used by localization')),
                ('tenant', models.ForeignKey(help_text='ID of the tenant the object belongs to', on_delete=models.CASCADE, to='main.tenant')),
            ],
        ),
        migrations.CreateModel(
            name='ServicePlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the object was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The time at which the object was last updated')),
                ('name', models.CharField(blank=True, default='', help_text='The name of the service plan', max_length=255)),
                ('base_schema', models.JSONField(blank=True, help_text='JSON schema of the survey from the controller', null=True)),
                ('modified_schema', models.JSONField(blank=True, help_text='Modified JSON schema for the service plan', null=True)),
                ('base_sha256', models.TextField(blank=True, default='', editable=False, help_text='SHA256 of the base schema')),
                ('outdated', models.BooleanField(default=False, editable=False, help_text='Whether or not the base schema is outdated. The portfolio item is not orderable if the base schema is outdated.')),
                ('outdated_changes', models.TextField(blank=True, default='', editable=False, help_text='Changes of the base schema from inventory since last edit')),
                ('inventory_service_plan_ref', models.CharField(help_text='Corresponding service plan from inventory-api', max_length=64, null=True)),
                ('service_offering_ref', models.CharField(help_text='Corresponding service offering from inventory-api', max_length=64, null=True)),
                ('portfolio_item', models.ForeignKey(help_text='ID of the portfolio item', on_delete=models.CASCADE, to='main.portfolioitem')),
                ('tenant', models.ForeignKey(help_text='ID of the tenant the object belongs to', on_delete=models.CASCADE, to='main.tenant')),
            ],
            bases=(
                KeycloakMixin,
                models.Model
            ),
        ),
        migrations.CreateModel(
            name='ServiceOfferingNode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the object was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The time at which the object was last updated')),
                ('source_created_at', models.DateTimeField(editable=False, null=True)),
                ('source_updated_at', models.DateTimeField(editable=False, null=True)),
                ('source_ref', models.CharField(max_length=32)),
                ('extra', models.JSONField()),
                ('root_service_offering', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='root_service_offering', to='main.serviceoffering')),
                ('service_inventory', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to='main.serviceinventory')),
                ('service_offering', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to='main.serviceoffering')),
                ('source', models.ForeignKey(help_text='ID of the source that this object belongs to', on_delete=models.CASCADE, to='main.source')),
                ('tenant', models.ForeignKey(help_text='ID of the tenant the object belongs to', on_delete=models.CASCADE, to='main.tenant')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='serviceoffering',
            name='source',
            field=models.ForeignKey(
                help_text='ID of the source that this object belongs to',
                on_delete=models.CASCADE,
                to='main.source'),
        ),
        migrations.AddField(
            model_name='serviceoffering',
            name='tenant',
            field=models.ForeignKey(help_text='ID of the tenant the object belongs to', on_delete=models.CASCADE, to='main.tenant'),
        ),
        migrations.AddField(
            model_name='serviceinventory',
            name='source',
            field=models.ForeignKey(help_text='ID of the source that this object belongs to', on_delete=models.CASCADE, to='main.source'),
        ),
        migrations.AddField(
            model_name='serviceinventory',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
        migrations.AddField(
            model_name='serviceinventory',
            name='tenant',
            field=models.ForeignKey(help_text='ID of the tenant the object belongs to', on_delete=models.CASCADE, to='main.tenant'),
        ),
        migrations.CreateModel(
            name='ServiceInstance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the object was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The time at which the object was last updated')),
                ('source_created_at', models.DateTimeField(editable=False, null=True)),
                ('source_updated_at', models.DateTimeField(editable=False, null=True)),
                ('source_ref', models.CharField(max_length=32)),
                ('name', models.CharField(blank=True, max_length=255)),
                ('extra', models.JSONField(null=True)),
                ('external_url', models.CharField(blank=True, max_length=255)),
                ('service_inventory', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to='main.serviceinventory')),
                ('service_offering', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to='main.serviceoffering')),
                ('service_plan', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to='main.inventoryserviceplan')),
                ('source', models.ForeignKey(help_text='ID of the source that this object belongs to', on_delete=models.CASCADE, to='main.source')),
                ('tenant', models.ForeignKey(help_text='ID of the tenant the object belongs to', on_delete=models.CASCADE, to='main.tenant')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Request',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the object was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The time at which the object was last updated')),
                ('keycloak_id', models.CharField(max_length=255, null=True)),
                ('name', models.CharField(help_text='Name of the request to be created', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Describe the request in more details')),
                ('state', models.CharField(choices=[('pending', 'Pending'), ('skipped', 'Skipped'), ('started', 'Started'), ('notified', 'Notified'), ('completed', 'Completed'), ('canceled', 'Canceled'), ('failed', 'Failed')], default='pending', editable=False, help_text='The state of the request, must be one of the predefined values', max_length=10)),
                ('decision', models.CharField(choices=[('undecided', 'Undecided'), ('approved', 'Approved'), ('denied', 'Denied'), ('canceled', 'Canceled'), ('error', 'Error')], default='undecided', editable=False, help_text='Approval decision, must be one of the predefined values', max_length=10)),
                ('reason', models.TextField(blank=True, editable=False, help_text='Optional reason for the decision, present normally when the decision is denied')),
                ('process_ref', models.CharField(editable=False, max_length=128)),
                ('group_name', models.CharField(editable=False, help_text='Name of approver group(s) assigned to approve this request', max_length=128)),
                ('group_ref', models.CharField(db_index=True, editable=False, max_length=128)),
                ('notified_at', models.DateTimeField(editable=False, help_text='Time when a notification was sent to approvers', null=True)),
                ('finished_at', models.DateTimeField(editable=False, help_text='Time when the request was finished (skipped, canceled, or completed)', null=True)),
                ('number_of_children', models.SmallIntegerField(default=0, editable=False, help_text='Number of child requests')),
                ('number_of_finished_children', models.SmallIntegerField(default=0, editable=False, help_text='Number of finished child requests')),
                ('parent', models.ForeignKey(help_text='ID of the parent group if present', null=True, on_delete=models.CASCADE, related_name='subrequests', to='main.request')),
                ('request_context', models.ForeignKey(null=True, on_delete=models.SET_NULL, to='main.requestcontext')),
                ('tenant', models.ForeignKey(help_text='ID of the tenant the object belongs to', on_delete=models.CASCADE, to='main.tenant')),
                ('user', models.ForeignKey(null=True, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('workflow', models.ForeignKey(help_text='ID of the workflow that the request belongs to. Present only if the request is a leaf node', null=True, on_delete=models.SET_NULL, to='main.workflow')),
            ],
            options={
                'abstract': False,
            },
            bases=(KeycloakMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ProgressMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the object was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The time at which the object was last updated')),
                ('level', models.CharField(choices=[('Info', 'Info'), ('Error', 'Error'), ('Warning', 'Warning'), ('Debug', 'Debug')], default='Info', editable=False, help_text='One of the predefined levels', max_length=10)),
                ('received_at', models.DateTimeField(auto_now_add=True, help_text='Message received at')),
                ('message', models.TextField(blank=True, default='', help_text='The message content')),
                ('messageable_type', models.CharField(editable=False, help_text='Identify order or order item that this message belongs to', max_length=64)),
                ('messageable_id', models.IntegerField(editable=False, help_text='ID of the order or order item')),
                ('tenant', models.ForeignKey(help_text='ID of the tenant the object belongs to', on_delete=models.CASCADE, to='main.tenant')),
            ],
            bases=(KeycloakMixin, models.Model),
        ),
        migrations.AddField(
            model_name='portfolioitem',
            name='tenant',
            field=models.ForeignKey(help_text='ID of the tenant the object belongs to', on_delete=models.CASCADE, to='main.tenant'),
        ),
        migrations.AddField(
            model_name='portfolioitem',
            name='user',
            field=models.ForeignKey(help_text='ID of the user who created this object', null=True, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='portfolio',
            name='tenant',
            field=models.ForeignKey(help_text='ID of the tenant the object belongs to', on_delete=models.CASCADE, to='main.tenant'),
        ),
        migrations.AddField(
            model_name='portfolio',
            name='user',
            field=models.ForeignKey(help_text='ID of the user who created this object', null=True, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the object was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The time at which the object was last updated')),
                ('name', models.CharField(help_text='Name of the portfolio item or order process', max_length=512)),
                ('state', models.CharField(choices=[('Approval Pending', 'Pending'), ('Approved', 'Approved'), ('Canceled', 'Canceled'), ('Completed', 'Completed'), ('Created', 'Created'), ('Denied', 'Denied'), ('Failed', 'Failed'), ('Ordered', 'Ordered')], default='Created', editable=False, help_text='Current state of this order item', max_length=20)),
                ('order_request_sent_at', models.DateTimeField(editable=False, help_text='The time at which the order request was sent to the catalog inventory service', null=True)),
                ('completed_at', models.DateTimeField(editable=False, help_text='The time at which the order item completed', null=True)),
                ('count', models.SmallIntegerField(default=0, editable=False, help_text='Item count')),
                ('inventory_task_ref', models.CharField(help_text='Task reference from inventory-api', max_length=64, null=True)),
                ('inventory_service_plan_ref', models.CharField(help_text='Corresponding service plan from inventory-api', max_length=64, null=True)),
                ('service_instance_ref', models.CharField(help_text='Corresponding service instance from inventory-api', max_length=64, null=True)),
                ('service_parameters', models.JSONField(blank=True, help_text='Sanitized JSON object with provisioning parameters', null=True)),
                ('service_parameters_raw', models.JSONField(blank=True, help_text='Raw JSON object with provisioning parameters', null=True)),
                ('provider_control_parameters', models.JSONField(blank=True, help_text='The provider specific parameters needed to provision this service. This might include namespaces, special keys.', null=True)),
                ('context', models.JSONField(blank=True, null=True)),
                ('artifacts', models.JSONField(blank=True, help_text='Contains a prefix-stripped key/value object that contains all of the information exposed from product provisioning', null=True)),
                ('external_url', models.URLField(blank=True, help_text='The external url of the service instance used with relation to this order item')),
                ('order', models.ForeignKey(help_text='The order that the order item belongs to', on_delete=models.CASCADE, to='main.order')),
                ('portfolio_item', models.ForeignKey(help_text='Stores the portfolio item ID', on_delete=models.CASCADE, to='main.portfolioitem')),
                ('tenant', models.ForeignKey(help_text='ID of the tenant the object belongs to', on_delete=models.CASCADE, to='main.tenant')),
                ('user', models.ForeignKey(help_text='ID of the user who created this object', null=True, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            bases=(models.Model, MessageableMixin),
        ),
        migrations.AddField(
            model_name='order',
            name='tenant',
            field=models.ForeignKey(help_text='ID of the tenant the object belongs to', on_delete=models.CASCADE, to='main.tenant'),
        ),
        migrations.AddField(
            model_name='order',
            name='user',
            field=models.ForeignKey(help_text='ID of the user who created this object', null=True, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='NotificationType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('n_type', models.CharField(help_text='Name of the notification type', max_length=128, unique=True)),
                ('setting_schema', models.JSONField(blank=True, help_text='JSON schema of the notification type', null=True)),
                ('icon', models.ForeignKey(blank=True, help_text='ID of the icon image associated with this object', null=True, on_delete=models.SET_NULL, to='main.image')),
            ],
        ),
        migrations.AddField(
            model_name='notificationsetting',
            name='notification_type',
            field=models.ForeignKey(help_text='ID of the notification type', null=True, on_delete=models.CASCADE, to='main.notificationtype'),
        ),
        migrations.AddField(
            model_name='notificationsetting',
            name='tenant',
            field=models.ForeignKey(help_text='ID of the tenant the object belongs to', on_delete=models.CASCADE, to='main.tenant'),
        ),
        migrations.AddField(
            model_name='inventoryserviceplan',
            name='service_offering',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to='main.serviceoffering'),
        ),
        migrations.AddField(
            model_name='inventoryserviceplan',
            name='source',
            field=models.ForeignKey(help_text='ID of the source that this object belongs to', on_delete=models.CASCADE, to='main.source'),
        ),
        migrations.AddField(
            model_name='inventoryserviceplan',
            name='tenant',
            field=models.ForeignKey(help_text='ID of the tenant the object belongs to', on_delete=models.CASCADE, to='main.tenant'),
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('path', models.TextField(unique=True)),
                ('last_sync_time', models.DateTimeField()),
                ('parent', models.ForeignKey(null=True, on_delete=models.CASCADE, related_name='subgroups', to='main.group')),
                ('roles', models.ManyToManyField(to='main.role')),
            ],
        ),
        migrations.CreateModel(
            name='ApprovalRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the object was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The time at which the object was last updated')),
                ('approval_request_ref', models.CharField(default='', help_text='The ID of the approval submitted to approval-api', max_length=64)),
                ('reason', models.TextField(blank=True, default='', help_text='The reason for the current state')),
                ('request_completed_at', models.DateTimeField(editable=False, help_text='The time at which the approval request completed', null=True)),
                ('state', models.CharField(choices=[('undecided', 'Undecided'), ('approved', 'Approved'), ('canceled', 'Canceled'), ('denied', 'Denied'), ('failed', 'Failed')], default='undecided', editable=False, help_text='The state of the approval request (approved, denied, undecided, canceled, error)', max_length=10)),
                ('order', models.OneToOneField(help_text='The Order which the approval request belongs to', on_delete=models.CASCADE, to='main.order')),
                ('tenant', models.ForeignKey(help_text='ID of the tenant the object belongs to', on_delete=models.CASCADE, to='main.tenant')),
            ],
        ),
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the object was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The time at which the object was last updated')),
                ('operation', models.CharField(choices=[('notify', 'Notify'), ('start', 'Start'), ('skip', 'Skip'), ('memo', 'Memo'), ('approve', 'Approve'), ('deny', 'Deny'), ('cancel', 'Cancel'), ('error', 'Error')], default='memo', help_text='Action type, must be one of the predefined values. The request state will be updated according to the operation.', max_length=10)),
                ('comments', models.TextField(blank=True, help_text='Comments for the action')),
                ('request', models.ForeignKey(help_text='ID of the request that the action belongs to', on_delete=models.CASCADE, related_name='actions', to='main.request')),
                ('tenant', models.ForeignKey(help_text='ID of the tenant the object belongs to', on_delete=models.CASCADE, to='main.tenant')),
                ('user', models.ForeignKey(null=True, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddConstraint(
            model_name='workflow',
            constraint=models.CheckConstraint(check=models.Q(('name__length__gt', 0)), name='main_workflow_name_empty'),
        ),
        migrations.AddConstraint(
            model_name='workflow',
            constraint=models.UniqueConstraint(fields=('name', 'tenant', 'template'), name='main_workflow_name_unique'),
        ),
        migrations.AddConstraint(
            model_name='workflow',
            constraint=models.UniqueConstraint(fields=('internal_sequence', 'tenant'), name='main_workflow_internal_sequence_unique'),
        ),
        migrations.AddConstraint(
            model_name='template',
            constraint=models.CheckConstraint(check=models.Q(('title__length__gt', 0)), name='main_template_title_empty'),
        ),
        migrations.AddConstraint(
            model_name='template',
            constraint=models.UniqueConstraint(fields=('title', 'tenant'), name='main_template_title_unique'),
        ),
        migrations.AddConstraint(
            model_name='taglink',
            constraint=models.UniqueConstraint(fields=('app_name', 'object_type', 'tenant', 'workflow'), name='main_taglink_tag_unique'),
        ),
        migrations.AddIndex(
            model_name='serviceplan',
            index=models.Index(fields=['tenant', 'portfolio_item'], name='main_servic_tenant__bd89da_idx'),
        ),
        migrations.AddIndex(
            model_name='progressmessage',
            index=models.Index(fields=['tenant', 'messageable_id', 'messageable_type'], name='main_progre_tenant__e6daa2_idx'),
        ),
        migrations.AddConstraint(
            model_name='portfolioitem',
            constraint=models.CheckConstraint(check=models.Q(('name__length__gt', 0)), name='main_portfolioitem_name_empty'),
        ),
        migrations.AddConstraint(
            model_name='portfolioitem',
            constraint=models.CheckConstraint(check=models.Q(('service_offering_ref__length__gt', 0)), name='main_portfolioitem_service_offering_empty'),
        ),
        migrations.AddConstraint(
            model_name='portfolio',
            constraint=models.CheckConstraint(check=models.Q(('name__length__gt', 0)), name='main_portfolio_name_empty'),
        ),
        migrations.AddConstraint(
            model_name='portfolio',
            constraint=models.UniqueConstraint(fields=('name', 'tenant'), name='main_portfolio_name_unique'),
        ),
        migrations.AddIndex(
            model_name='orderitem',
            index=models.Index(fields=['tenant', 'user'], name='main_orderi_tenant__57608b_idx'),
        ),
        migrations.AddConstraint(
            model_name='orderitem',
            constraint=models.CheckConstraint(check=models.Q(('name__length__gt', 0)), name='main_orderitem_name_empty'),
        ),
        migrations.AddConstraint(
            model_name='orderitem',
            constraint=models.UniqueConstraint(fields=('name', 'tenant', 'order', 'portfolio_item'), name='main_orderitem_name_unique'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['tenant', 'user'], name='main_order_tenant__9f158a_idx'),
        ),
        migrations.AddConstraint(
            model_name='notificationtype',
            constraint=models.CheckConstraint(check=models.Q(('n_type__length__gt', 0)), name='main_notificationtype_n_type_empty'),
        ),
        migrations.AddConstraint(
            model_name='notificationsetting',
            constraint=models.CheckConstraint(check=models.Q(('name__length__gt', 0)), name='main_notificationsetting_name_empty'),
        ),
        migrations.AddConstraint(
            model_name='notificationsetting',
            constraint=models.UniqueConstraint(fields=('name', 'tenant'), name='main_notificationsetting_name_unique'),
        ),
        migrations.AddIndex(
            model_name='approvalrequest',
            index=models.Index(fields=['tenant', 'order'], name='main_approv_tenant__9d790f_idx'),
        ),
        migrations.RunPython(code=upgrade)
    ]
