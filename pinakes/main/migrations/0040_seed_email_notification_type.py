import base64
import os
from django.conf import settings
from django.db import migrations, transaction
from django.db.models.fields.files import ImageFieldFile, FileField

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


def create_notification_type(apps, schema_editor):
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

    with transaction.atomic():
        NotificationType.objects.using(db_alias).create(
            n_type="email",
            setting_schema=SCHEMA,
            icon=Image.objects.using(db_alias).create(file=icon_file),
        )


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0039_remove_template_process_setting_and_more"),
    ]

    operations = [
        migrations.RunPython(create_notification_type),
    ]
