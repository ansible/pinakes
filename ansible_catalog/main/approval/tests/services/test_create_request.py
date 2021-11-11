""" Module to test creating requests """
from unittest.mock import Mock
import pytest
from ansible_catalog.main.tests.factories import default_tenant
from ansible_catalog.main.approval.tests.factories import WorkflowFactory
from ansible_catalog.main.approval.services.create_request import CreateRequest
from ansible_catalog.main.approval.services.link_workflow import FindWorkflows


@pytest.mark.django_db
def test_create_request_no_workflow(mocker):
    """Test to create a new request with no workflow"""

    service = _prepare_service(mocker)
    request = service.process().request
    _assert_request(request)


@pytest.mark.django_db
def test_create_request_one_workflow(mocker):
    """Test to create a new request with one workflow but no group"""

    workflow = WorkflowFactory()
    mocker.patch.object(
        FindWorkflows, "process", return_value=Mock(workflows=(workflow,))
    )
    service = _prepare_service(mocker)
    request = service.process().request
    _assert_request(request)


@pytest.mark.django_db
def test_create_request_one_workflow_groups(mocker):
    """Test to create a new request with one workflow multiple groups"""

    workflow = WorkflowFactory(
        group_refs=({"name": "n1", "uuid": "u1"}, {"name": "n2", "uuid": "u2"})
    )
    mocker.patch.object(
        FindWorkflows, "process", return_value=Mock(workflows=(workflow,))
    )
    service = _prepare_service(mocker)
    request = service.process().request
    _assert_request(request, num_children=2, group_name="n1,n2")
    _assert_request(request.requests[0], group_name="n1", workflow=workflow)
    _assert_request(request.requests[1], group_name="n2", workflow=workflow)


@pytest.mark.django_db
def test_create_request_workflows_groups(mocker):
    """Test to create a new request with workflows and groups"""

    workflow1 = WorkflowFactory(group_refs=({"name": "n1", "uuid": "u1"},))
    workflow2 = WorkflowFactory(group_refs=({"name": "n2", "uuid": "u2"},))
    mocker.patch.object(
        FindWorkflows,
        "process",
        return_value=Mock(workflows=(workflow1, workflow2)),
    )
    service = _prepare_service(mocker)
    request = service.process().request
    _assert_request(request, num_children=2, group_name="n1,n2")
    _assert_request(request.requests[0], group_name="n1", workflow=workflow1)
    _assert_request(request.requests[1], group_name="n2", workflow=workflow2)


def _prepare_service(mocker):
    mocker.patch("django_rq.enqueue", return_value=Mock(id=123))
    tenant = default_tenant()
    service = CreateRequest(
        {
            "name": "test",
            "description": "description",
            "content": {"param": "val"},
            "tenant": tenant,
        }
    )
    return service


def _assert_request(request, num_children=0, group_name="", workflow=None):
    assert request.name == "test"
    assert request.description == "description"
    assert request.state == "pending"
    assert request.decision == "undecided"
    assert request.number_of_children == num_children
    assert request.workflow == workflow
    assert request.group_name == group_name
