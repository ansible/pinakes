from django.conf import settings

from insights_analytics_collector import Package as InsightsAnalyticsPackage


class Package(InsightsAnalyticsPackage):
    PAYLOAD_CONTENT_TYPE = "application/vnd.redhat.pinakes.filename+tgz"

    def _tarname_base(self):
        timestamp = self.collector.gather_until
        # TODO: replace test with {settings.SYSTEM_UUID}
        return f'pinake-{timestamp.strftime("%Y-%m-%d-%H%M%S%z")}'

    def get_ingress_url(self):
        return getattr(settings, "PINAKES_INSIGHTS_URL", None)

    def shipping_auth_mode(self):
        return InsightsAnalyticsPackage.SHIPPING_AUTH_CERTIFICATES

    def _get_http_request_headers(self):
        return {
            "Content-Type": self.PAYLOAD_CONTENT_TYPE,
            # TODO: add version string later
            "User-Agent": "Pinakes-metrics-agent",
        }
