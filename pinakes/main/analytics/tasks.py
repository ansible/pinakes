""" Tasks for metrics collection """
import logging
from django.conf import settings
from django.utils.timezone import now
from rest_framework.fields import DateTimeField

from pinakes.main.analytics import core

logger = logging.getLogger("inventory")


def gather_analytics():
    last_gather = settings.AUTOMATION_ANALYTICS_LAST_GATHER
    last_time = (
        DateTimeField().to_internal_value(last_gather.value)
        if last_gather and last_gather.value
        else None
    )
    gather_time = now()

    if not last_time or (
        (gather_time - last_time).total_seconds()
        > settings.AUTOMATION_ANALYTICS_GATHER_INTERVAL
    ):
        core.gather()
