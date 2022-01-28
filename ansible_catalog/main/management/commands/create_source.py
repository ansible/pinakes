from ansible_catalog.main.models import Source, Tenant
from django.core.management.base import BaseCommand

DEFAULT_SOURCE_NAME = "source_1"


class Command(BaseCommand):
    help = "Create the source if it doesn't exists"

    def add_arguments(self, parser):
        parser.add_argument(
            "name",
            default=DEFAULT_SOURCE_NAME,
            nargs="?",
            help=f"Optional custom name for the source. Default: {DEFAULT_SOURCE_NAME}",
        )

    def handle(self, *args, **kwargs):
        name = kwargs["name"]

        if Source.objects.count() == 0:
            Source.objects.create(name=name, tenant=Tenant.current())
            self.stdout.write(
                self.style.SUCCESS(f'Source "{name}" succesfully created')
            )
        else:
            self.stdout.write(self.style.NOTICE(f"The source already exists"))
