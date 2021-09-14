""" Background tasks for inventory """
import logging
from rq import get_current_job

from main.inventory.task_utils.refresh_inventory import RefreshInventory
from main.inventory.task_utils.launch_job import LaunchJob
from main.catalog.services.finish_order_item import FinishOrderItem

logger = logging.getLogger("inventory")


def refresh_task(tenant_id, source_id):
    """Run the Refresh task"""
    logger.info("Starting Inventory Refresh")
    obj = RefreshInventory(tenant_id, source_id)
    obj.process()
    logger.info("Finished Inventory Refresh")


def launch_tower_task(slug, body):
    """Launch a job on the tower"""
    job = get_current_job()
    try:
        logger.info("Starting job %s", job.id)
        obj = LaunchJob(slug, body).process()
        logger.info(obj)
        FinishOrderItem(
            inventory_task_ref=job.id, artifacts=obj["artifacts"]
        ).process()

        logger.info("Job successfully finished %s", job.id)
    except Exception as exc:
        logger.error("Job failed %s exception %s", job.id, str(exc))
        FinishOrderItem(
            inventory_task_ref=job.id, error_msg=str(exc)
        ).process()
        raise
