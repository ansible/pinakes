import logging

from datetime import datetime
from django.conf import settings
import django_rq
from django_rq.management.commands import rqscheduler

scheduler = django_rq.get_scheduler()
logger = logging.getLogger("rq.worker")


def cancel_scheduled_jobs():
    """Cancel any existing jobs in the scheduler when the app starts up"""
    for job in scheduler.get_jobs():
        if not job.is_canceled:
            logger.info("Cancelling scheduled cron job %s", job)
            scheduler.cancel(job)


class Command(rqscheduler.Command):
    """Command to schedule cron jobs"""

    def handle(self, *args, **kwargs):
        logger.info("Clearing scheduled cron jobs:")
        cancel_scheduled_jobs()

        for job in settings.STARTUP_RQ_JOBS:
            logger.info("Run startup job: %s", job)
            scheduler.enqueue_at(
                datetime.utcnow(),
                job,
            )

        logger.info("Start to schedule cron jobs defined in settings:")

        for cronjob in settings.RQ_CRONJOBS:
            if type(cronjob) is dict:  # with params
                args = []
                options = cronjob
            else:
                args = cronjob
                options = {}

            job = scheduler.cron(*args, **options)
            logger.info("Job {} is scheduled".format(job))

        super(Command, self).handle(*args, **kwargs)
