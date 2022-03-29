import json
from pathlib import Path

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection

from rest_framework.fields import DateTimeField

from insights_analytics_collector import Collector
from pinakes.main.analytics.package import Package


class AnalyticsCollector(Collector):
    ANALYTICS_LAST_GATHER_FILE = "analytics_last_gather"
    ANALYTICS_LAST_ENTRIES_FILE = "analytics_last_entries"

    @staticmethod
    def db_connection():
        return connection

    @staticmethod
    def _package_class():
        return Package

    def get_last_gathering(self):
        return self._last_gathering()

    def _is_shipping_configured(self):
        if not settings.PINAKES_INSIGHTS_TRACKING_STATE:
            self.logger.error(
                "Insights for Automation Service Catalog is not enabled. \
                Use --dry-run to gather locally without sending."
            )
            return False

        if not settings.PINAKES_INSIGHTS_URL:
            self.logger.error("AUTOMATION_ANALYTICS_URL is not set")
            return False

        if not settings.PINAKES_INSIGHTS_USERNAME:
            self.logger.error("PINAKES_INSIGHTS_USERNAME is not set")
            return False

        if not settings.PINAKES_INSIGHTS_PASSWORD:
            self.logger.error("PINAKES_INSIGHTS_PASSWORD is not set")
            return False

        return True

    def _is_valid_license(self):
        # TODO: need license information and validation logics
        return True

    def _last_gathering(self):
        last_gathering_file = Path(self.ANALYTICS_LAST_GATHER_FILE)
        last_gathering_file.touch(exist_ok=True)

        with open(self.ANALYTICS_LAST_GATHER_FILE, "r") as reader:
            last_gather = reader.read()

        return (
            DateTimeField().to_internal_value(last_gather)
            if last_gather
            else None
        )

    def _load_last_gathered_entries(self):
        last_entries_file = Path(self.ANALYTICS_LAST_ENTRIES_FILE)
        last_entries_file.touch(exist_ok=True)

        with open(self.ANALYTICS_LAST_ENTRIES_FILE, "r") as reader:
            last_entries = reader.read()

        json_last_entries = json.loads(last_entries) if last_entries else {}
        for key, value in json_last_entries.items():
            json_last_entries[key] = DateTimeField().to_internal_value(value)

        return json_last_entries

    def _save_last_gathered_entries(self, last_gathered_entries):
        self.logger.info(f"Save last_entries: {last_gathered_entries}")

        with open(self.ANALYTICS_LAST_ENTRIES_FILE, "w") as writer:
            writer.write(
                json.dumps(
                    last_gathered_entries["keys"], cls=DjangoJSONEncoder
                )
            )

    def _save_last_gather(self):
        self.logger.info(f"Save last_gather: {self.gather_until}")
        with open(self.ANALYTICS_LAST_GATHER_FILE, "w") as writer:
            writer.write(self.gather_until.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
