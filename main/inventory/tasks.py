""" Background tasks for inventory """
import logging
from main.inventory.task_utils.refresh_inventory import RefreshInventory
from main.inventory.task_utils.launch_job import LaunchJob

logger = logging.getLogger("inventory")


def refresh_task(tenant_id, source_id):
    """Run the Refresh task"""
    logger.info("Starting Inventory Refresh")
    obj = RefreshInventory(tenant_id, source_id)
    result = obj.process()
    logger.info("Finished Inventory Refresh")
    return result


def launch_tower_task(slug, body):
    """Launch a job on the tower"""
    logger.info("Launching job")
    obj = LaunchJob(slug, body).process()
    logger.info(obj)
    logger.info("Job finished")
    return obj
