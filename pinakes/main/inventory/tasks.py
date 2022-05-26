"""Background tasks for inventory"""
import logging
from rq import get_current_job

from pinakes.main.inventory.task_utils.check_source_availability import (
    CheckSourceAvailability,
)
from pinakes.main.inventory.task_utils.refresh_inventory import (
    RefreshInventory,
)
from pinakes.main.inventory.task_utils.launch_job import (
    LaunchJob,
)
from pinakes.main.catalog.services.finish_order_item import (
    FinishOrderItem,
)
from pinakes.main.catalog.services.update_service_plans import (
    UpdateServicePlans,
)
from pinakes.main.models import Source

logger = logging.getLogger("inventory")


def refresh_all_sources():
    """Task to refresh all sources, used by cron jobs"""
    for source in Source.objects.all():
        logger.info("Refreshing source %s", source.name)
        refresh_task(source.tenant_id, source.id)


def refresh_task(tenant_id, source_id):
    """Run the Refresh task"""
    logger.info("First checking its availability")
    svc = CheckSourceAvailability(source_id)
    svc.process()

    if svc.source.availability_status == "available":
        logger.info("Starting Inventory Refresh")
        obj = RefreshInventory(source_id)
        obj.process()
        logger.info("Updating Service Plans")
        upd_sp = UpdateServicePlans(tenant_id)
        upd_sp.process()
        logger.info(f"Updated {upd_sp.updated} Service Plans")
        logger.info("Finished Inventory Refresh")
    else:
        logger.error(
            "Source %s[%s] is unavailable, cannot refresh it",
            svc.source.name,
            svc.tower.url,
        )


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
