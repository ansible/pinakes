from django.core.management import BaseCommand

from pinakes.main.approval.models import NotificationSetting


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.re_encrypt_notification_setttings()

    def re_encrypt_notification_setttings(self):
        self.stdout.write("Re-encrypting notification settings...")
        items = NotificationSetting.objects.all()
        rows_updated = NotificationSetting.objects.bulk_update(
            items, ["settings"]
        )
        self.stdout.write(self.style.SUCCESS(f"Updated {rows_updated} rows."))
