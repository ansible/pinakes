import logging

from datetime import datetime
from django.conf import settings
import django_rq
from django_rq.management.commands import rqscheduler

from ansible_catalog.main.models import Source
from ansible_catalog.main.inventory.tasks import refresh_task
from ansible_catalog.main.inventory.tasks import refresh_all_sources
from ansible_catalog.main.auth.tasks import sync_external_groups


scheduler = django_rq.get_scheduler()
logger = logging.getLogger("rq.worker")


def clear_scheduled_jobs():
    # Delete any existing jobs in the scheduler when the app starts up
    for job in scheduler.get_jobs():
        logger.info("Deleting scheduled cron job %s", job)
        job.delete()


def register_refresh_inventories_jobs():
    source = Source.objects.first()
    logger.info("schedule cron jobs for source %d:" % source.id)

    scheduler.cron(
        "*/30 * * * *",
        func=refresh_task,
        args=[
            source.tenant_id,
            source.id,
        ],
    )


def register_sync_groups_jobs():
    logger.info("schedule cron jobs for syncing groups:")

    scheduler.cron(
        "*/30 * * * *",
        func=sync_external_groups,
        queue_name="default",
    )


def init_first_refresh_inventory_job():
    source = Source.objects.first()
    logger.info("Initial refresh inventory for source %d", source.id)

    scheduler.enqueue_at(
        datetime.utcnow(),
        refresh_task,
        source.tenant_id,
        source.id,
    )


def init_first_sync_groups_job():
    logger.info("Initial sync groups:")
    scheduler.enqueue_at(
        datetime.utcnow(),
        sync_external_groups,
    )


class Command(rqscheduler.Command):
    def handle(self, *args, **kwargs):
        # This is necessary to prevent dupes
        logger.info("Clearing scheduled cron jobs:")
        clear_scheduled_jobs()

        logger.info("Start to run initial jobs:")
        init_first_refresh_inventory_job()
        init_first_sync_groups_job()

        logger.info("Start to schedule cron jobs defined in settings:")

        # Replace following jobs with the one defined in setting
        # register_refresh_inventories_jobs()
        # register_sync_groups_jobs()

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
