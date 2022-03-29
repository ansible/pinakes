from django.conf import settings
from django.db import connection

from insights_analytics_collector import Collector
from pinakes.main.analytics.package import Package


class AnalyticsCollector(Collector):
    @staticmethod
    def db_connection():
        return connection

    @staticmethod
    def _package_class():
        return Package

    def _is_shipping_configured(self):
        if not settings.PINAKES_INSIGHTS_TRACKING_STATE:
            self.logger.error(
                "Insights for Automation Service Catalog is not enabled. Use --dry-run to gather locally without sending."
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
        return getattr(settings, "PINAKES_ANALYTICS_LAST_GATHER", None)

    def _load_last_gathered_entries(self):
        return getattr(settings, "PINAKES_ANALYTICS_LAST_ENTRIES", {})

    def _save_last_gathered_entries(self, last_gathered_entries):
        settings.PINAKES_ANALYTICS_LAST_ENTRIES = last_gathered_entries

    def _save_last_gather(self):
        settings.PINAKES_ANALYTICS_LAST_GATHER = self.gather_until
