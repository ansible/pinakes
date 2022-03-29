""" Tasks for metrics collection """
import logging
from django.conf import settings
from django.utils.timezone import now
from rest_framework.fields import DateTimeField

from pinakes.main.analytics.collector import AnalyticsCollector
from pinakes.main.analytics import analytics_collectors

logger = logging.getLogger("analytics")


def gather_analytics():
    collector = AnalyticsCollector(
        collector_module=analytics_collectors,
        collection_type="scheduled",
        logger=logger,
    )

    last_gather = settings.PINAKES_ANALYTICS_LAST_GATHER
    last_time = (
        DateTimeField().to_internal_value(last_gather.value)
        if last_gather and last_gather.value
        else None
    )

    logger.info("last gather time: %s", last_gather)
    logger.info(
        "last gather entries: %s", settings.PINAKES_ANALYTICS_LAST_ENTRIES
    )

    collector.gather(since=last_time)
