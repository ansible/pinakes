""" Tasks for metrics collection """
import logging
import django_rq
from rq import Queue
from rq.job import Job
from rq import get_current_job
from rq import exceptions

from django.utils.timezone import make_aware

from pinakes.main.analytics.collector import AnalyticsCollector
from pinakes.main.analytics import analytics_collectors

logger = logging.getLogger("analytics")


def gather_analytics():
    collector = AnalyticsCollector(
        collector_module=analytics_collectors,
        collection_type="scheduled",
        logger=logger,
    )

    last_gather = get_last_gather()
    saved_last_gather = make_aware(last_gather) if last_gather else None

    # save last gathered job info in current job's meta
    job = get_current_job()
    job.meta["last_gather"] = saved_last_gather
    job.save_meta()

    collector.gather(since=saved_last_gather)


def get_last_gather():
    connection = django_rq.get_connection()
    queue = Queue(connection=connection)

    last_finished_job = get_last_successful_gather_job(
        queue.finished_job_registry, connection
    )
    last_canceled_job = get_last_successful_gather_job(
        queue.canceled_job_registry, connection
    )

    if last_canceled_job:
        logger.info(
            "last canceled job: %s, %s",
            last_canceled_job.id,
            last_canceled_job.ended_at,
        )
    if last_finished_job:
        logger.info(
            "last finished job: %s, %s",
            last_finished_job.id,
            last_finished_job.ended_at,
        )

    return (
        last_finished_job.ended_at
        if last_finished_job
        else last_canceled_job.ended_at
        if last_canceled_job
        else None
    )


def get_last_successful_gather_job(job_registry, connection):
    job_ids = job_registry.get_job_ids()

    while len(job_ids) > 0:
        job_id = job_ids.pop(-1)
        try:
            job = Job.fetch(job_id, connection)
        except exceptions.NoSuchJobError:
            logger.warning(f"No job with id: {job_id}")
            continue

        if job.ended_at and job.func_name.endswith("gather_analytics"):
            return job

    return None
