"""Background tasks for inventory"""
import logging
from rq import get_current_job
from pinakes.main.approval.services.create_action import (
    CreateAction,
)
from pinakes.main.approval.services.process_root_request import (
    ProcessRootRequest,
)
from pinakes.main.approval.services.email_notification import EmailNotification
from pinakes.main.approval.models import Action

logger = logging.getLogger("approval")


def process_root_task(root_id, workflow_ids):
    """Process root request"""
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


def email_task(request_id):
    """Send emails to approvers"""
    job = get_current_job()
    try:
        logger.info(
            "Job %s: Sending email notification for request %d",
            job.id,
            request_id,
        )
        EmailNotification(request_id).send_emails()
    except Exception as exc:
        logger.error("Job %s failed with exception %s", job.id, str(exc))
        raise
