from django.conf import settings

from insights_analytics_collector import Package as InsightsAnalyticsPackage


class Package(InsightsAnalyticsPackage):
    PAYLOAD_CONTENT_TYPE = "application/vnd.redhat.pinakes.filename+tgz"

    def _tarname_base(self):
        timestamp = self.collector.gather_until
        # TODO: replace test with {settings.SYSTEM_UUID}
        return f'test-{timestamp.strftime("%Y-%m-%d-%H%M%S%z")}'

    def get_ingress_url(self):
        return getattr(settings, "PINAKES_INSIGHTS_URL", None)

    def _get_rh_user(self):
        return getattr(settings, "PINAKES_INSIGHTS_USERNAME", None)

    def _get_rh_password(self):
        return getattr(settings, "PINAKES_INSIGHTS_PASSWORD", None)

    def _get_http_request_headers(self):
        return {
            "Content-Type": self.PAYLOAD_CONTENT_TYPE,
            "User-Agent": "python-requests/2.25.1",
        }
