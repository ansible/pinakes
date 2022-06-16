"""Module to test processing root requests"""
from unittest.mock import Mock, call
import pytest
from pinakes.main.approval.tests.factories import (
    NotificationSettingFactory,
    TemplateFactory,
    WorkflowFactory,
    RequestFactory,
)
from pinakes.main.approval.services.process_root_request import (
    ProcessRootRequest,
)
from pinakes.main.approval.tasks import start_request_task
from pinakes.main.catalog.services.handle_approval_events import (
    HandleApprovalEvents,
)
from pinakes.main.approval.services.email_notification import (
    EmailNotification,
)


@pytest.mark.django_db
def test_process_request_no_workflow(mocker):
    """Test to create a new request with no workflow"""

    service = _prepare_service(mocker, [])
    request = service.process().request
    _assert_request(request, state="completed", decision="approved")


@pytest.mark.django_db
def test_process_request_one_workflow(mocker):
    """Test to create a new request with one workflow but no group"""

    workflow = WorkflowFactory()
    service = _prepare_service(mocker, [workflow.id])
    request = service.process().request
    _assert_request(
        request, state="notified", group_name="<NO_GROUP>", workflow=workflow
    )


@pytest.mark.django_db
def test_process_request_one_workflow_one_group(mocker):
    """Test to create a new request with one workflow and one group"""

    add_permissions = mocker.patch(
        "pinakes.main.common.tasks.add_group_permissions",
        return_value=None,
    )
    validations = mocker.patch(
        "pinakes.main.approval.validations.runtime_validate_group",
        return_value=True,
    )
    mocker.patch.object(EmailNotification, "process")

    template = TemplateFactory(process_method=NotificationSettingFactory())
    workflow = WorkflowFactory(
        template=template, group_refs=({"name": "n1", "uuid": "u1"},)
    )
    service = _prepare_service(mocker, [workflow.id])
    request = service.process().request
    _assert_request(
        request, state="started", group_name="n1", workflow=workflow
    )
    assert add_permissions.call_count == 1
    assert validations.call_count == 1


@pytest.mark.django_db
def test_process_request_one_workflow_groups(mocker):
    """Test to create a new request with one workflow multiple groups"""

    add_permissions = mocker.patch(
        "pinakes.main.common.tasks.add_group_permissions",
        return_value=None,
    )
    enqueue = mocker.patch("django_rq.enqueue", return_value=Mock(id=123))

    workflow = WorkflowFactory(
        group_refs=({"name": "n1", "uuid": "u1"}, {"name": "n2", "uuid": "u2"})
    )
    service = _prepare_service(mocker, [workflow.id])
    request = service.process().request
    _assert_request(request, num_children=2, group_name="n1,n2")
    _assert_request(request.requests[0], group_name="n1", workflow=workflow)
    _assert_request(request.requests[1], group_name="n2", workflow=workflow)
    enqueue.assert_has_calls(
        [
            call(start_request_task, request.requests[0].id),
            call(start_request_task, request.requests[1].id),
        ]
    )
    assert add_permissions.call_count == 2


@pytest.mark.django_db
def test_process_request_workflows_groups(mocker):
    """Test to create a new request with workflows and groups"""

    add_permissions = mocker.patch(
        "pinakes.main.common.tasks.add_group_permissions",
        return_value=None,
    )

    workflow1 = WorkflowFactory(group_refs=({"name": "n1", "uuid": "u1"},))
    workflow2 = WorkflowFactory()
    service = _prepare_service(mocker, [workflow1.id, workflow2.id])
    request = service.process().request

    request.refresh_from_db()
    _assert_request(
        request, state="notified", num_children=2, group_name="n1,<NO_GROUP>"
    )
    _assert_request(
        request.requests[0],
        state="notified",
        group_name="n1",
        workflow=workflow1,
    )
    _assert_request(
        request.requests[1],
        state="pending",
        group_name="<NO_GROUP>",
        workflow=workflow2,
    )
    assert add_permissions.call_count == 1


def _prepare_service(mocker, workflow_ids):
    request = RequestFactory(
        name="test", description="description", workflow=None
    )
    mocker.patch.object(HandleApprovalEvents, "process", return_value=None)
    service = ProcessRootRequest(request.id, workflow_ids)
    return service


def _assert_request(
    request,
    state="pending",
    decision="undecided",
    num_children=0,
    group_name="",
    workflow=None,
):
    assert request.name == "test"
    assert request.description == "description"
    assert request.state == state
    assert request.decision == decision
    assert request.number_of_children == num_children
    assert request.workflow == workflow
    assert request.group_name == group_name
