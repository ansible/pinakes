""" Background tasks for inventory """
import logging
from rq import get_current_job
from ansible_catalog.main.approval.services.create_action import CreateAction
from ansible_catalog.main.approval.models import Action

logger = logging.getLogger("approval")


def start_request_task(request_id):
    """Start an approval request"""
    job = get_current_job()
    try:
        logger.info("Starting approval request %s", job.id)
        CreateAction(
            request_id, {"operation": Action.Operation.START}
        ).process()
    except Exception as exc:
        logger.error("Job failed %s exception %s", job.id, str(exc))
        raise
