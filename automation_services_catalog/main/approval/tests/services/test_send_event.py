"""Module to test send events"""
import pytest

from automation_services_catalog.main.approval.tests.factories import (
    RequestFactory,
    WorkflowFactory,
)
from automation_services_catalog.main.approval.services.send_event import SendEvent
from automation_services_catalog.main.catalog.services.handle_approval_events import (
    HandleApprovalEvents,
)


@pytest.mark.django_db
def test_request_started(mocker):
    receive_service = mocker.patch.object(
        HandleApprovalEvents, "__init__", return_value=None
    )
    request = RequestFactory()

    mocker.patch.object(HandleApprovalEvents, "process", return_value=None)
    SendEvent(request, SendEvent.EVENT_REQUEST_STARTED).process()

    receive_service.assert_called_once_with(
        event=SendEvent.EVENT_REQUEST_STARTED,
        payload={"request_id": request.id},
    )


@pytest.mark.django_db
def test_request_finished(mocker):
    receive_service = mocker.patch.object(
        HandleApprovalEvents, "__init__", return_value=None
    )
    request = RequestFactory(decision="Approved", reason="Good")
    mocker.patch.object(HandleApprovalEvents, "process", return_value=None)
    SendEvent(request, SendEvent.EVENT_REQUEST_FINISHED).process()
    receive_service.assert_called_once_with(
        event=SendEvent.EVENT_REQUEST_FINISHED,
        payload={
            "request_id": request.id,
            "decision": "Approved",
            "reason": "Good",
        },
    )


@pytest.mark.django_db
def test_request_canceled(mocker):
    receive_service = mocker.patch.object(
        HandleApprovalEvents, "__init__", return_value=None
    )
    request = RequestFactory(decision="Canceled", reason="by user")
    mocker.patch.object(HandleApprovalEvents, "process", return_value=None)
    SendEvent(request, SendEvent.EVENT_REQUEST_CANCELED).process()
    receive_service.assert_called_once_with(
        event=SendEvent.EVENT_REQUEST_CANCELED,
        payload={"request_id": request.id, "reason": "by user"},
    )


@pytest.mark.django_db
def test_workflow_deleted(mocker):
    receive_service = mocker.patch.object(
        HandleApprovalEvents, "__init__", return_value=None
    )
    workflow = WorkflowFactory()
    mocker.patch.object(HandleApprovalEvents, "process", return_value=None)
    SendEvent(workflow.id, SendEvent.EVENT_WORKFLOW_DELETED).process()
    receive_service.assert_called_once_with(
        event=SendEvent.EVENT_WORKFLOW_DELETED,
        payload={"workflow_id": workflow.id},
    )
