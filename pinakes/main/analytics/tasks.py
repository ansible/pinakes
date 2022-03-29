""" Tasks for metrics collection """
import logging

from pinakes.main.analytics.collector import AnalyticsCollector
from pinakes.main.analytics import analytics_collectors

logger = logging.getLogger("analytics")


def gather_analytics():
    collector = AnalyticsCollector(
        collector_module=analytics_collectors,
        collection_type="scheduled",
        logger=logger,
    )

    collector.gather(since=collector.get_last_gathering())
