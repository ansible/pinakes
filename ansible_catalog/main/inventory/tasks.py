""" Background tasks for inventory """
import logging
from rq import get_current_job

from ansible_catalog.main.inventory.task_utils.check_source_availability import (
    CheckSourceAvailability,
)
from ansible_catalog.main.inventory.task_utils.refresh_inventory import (
    RefreshInventory,
)
from ansible_catalog.main.inventory.task_utils.launch_job import LaunchJob
from ansible_catalog.main.catalog.services.finish_order_item import (
    FinishOrderItem,
)
from ansible_catalog.main.catalog.services.update_service_plans import (
    UpdateServicePlans,
)
from ansible_catalog.main.models import Source

logger = logging.getLogger("inventory")


def check_all_source_status():
    """Task to check source status"""
    for source in Source.objects.all():
        logger.info("Checking source %s", source.name)
        svc = CheckSourceAvailability(source.tenant_id, source.id)
        svc.process()
    logger.info("Finished checking source status")


def refresh_all_sources():
    """Task to refresh all sources, used by cron jobs"""
    for source in Source.objects.all():
        logger.info("Refreshing source %s", source.name)
        refresh_task(source.tenant_id, source.id)


def refresh_task(tenant_id, source_id):
    """Run the Refresh task"""
    logger.info("Starting Inventory Refresh")
    obj = RefreshInventory(tenant_id, source_id)
    obj.process()
    logger.info("Updating Service Plans")
    upd_sp = UpdateServicePlans(tenant_id)
    upd_sp.process()
    logger.info(f"Updated {upd_sp.updated} Service Plans")
    logger.info("Finished Inventory Refresh")


def launch_tower_task(slug, body):
    """Launch a job on the tower"""
    job = get_current_job()
    try:
        logger.info("Starting job %s", job.id)
        svc = LaunchJob(slug, body).process()
        obj = svc.output

        logger.info("Job %s output: %s", job.id, obj)

        FinishOrderItem(
            inventory_task_ref=job.id,
            artifacts=obj["artifacts"],
            external_url=obj["url"],
            service_instance_ref=svc.service_instance_ref,
        ).process()

        logger.info("Job %s successfully finished", job.id)
    except Exception as exc:
        logger.error("Job failed %s exception %s", job.id, str(exc))
        FinishOrderItem(
            inventory_task_ref=job.id, error_msg=str(exc)
        ).process()
        raise
