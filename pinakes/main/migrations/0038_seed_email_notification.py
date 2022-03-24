from django.db import migrations, transaction

SCHEMA = {
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


def create_notification(apps, schema_editor):
    Notification = apps.get_model("main", "Notification")
    db_alias = schema_editor.connection.alias

    with transaction.atomic():
        Notification.objects.using(db_alias).create(
            name="email",
            setting_schema=SCHEMA,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0037_notification_and_more"),
    ]

    operations = [
        migrations.RunPython(create_notification),
    ]
