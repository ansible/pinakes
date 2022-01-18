""" Background tasks for inventory """
import logging
from rq import get_current_job
from ansible_catalog.main.approval.services.create_action import CreateAction
from ansible_catalog.main.approval.services.process_root_request import (
    ProcessRootRequest,
)
from ansible_catalog.main.approval.models import Action

logger = logging.getLogger("approval")


def process_root_task(root_id, workflow_ids):
    job = get_current_job()
    try:
        logger.info(
            "Job %s: Processing root request %d, workflow_ids %s",
            job.id,
            root_id,
            str(workflow_ids),
        )
        ProcessRootRequest(root_id, workflow_ids).process()
    except Exception as exc:
        logger.error("Job %s failed with exception %s", job.id, str(exc))
        raise


def start_request_task(request_id):
    """Start an approval request"""
    job = get_current_job()
    try:
        logger.info("Job %s: Starting approval request %d", job.id, request_id)
        CreateAction(
            request_id, {"operation": Action.Operation.START}
        ).process()
    except Exception as exc:
        logger.error("Job %s failed with exception %s", job.id, str(exc))
        raise
