from cryptography.fernet import Fernet

from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        key = Fernet.generate_key().decode("ascii")
        self.stdout.write(key)
