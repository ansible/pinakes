""" Module to test creating requests """
import pytest
from main.tests.factories import default_tenant
from main.approval.tests.factories import RequestFactory
from main.approval.services.create_request import CreateRequest
from main.approval.models import Request
from main.models import Tenant
from main.approval.services.send_event import SendEvent


@pytest.mark.django_db
def test_create_request_auto_approve(mocker):
    """Test to create a new request with auto approve"""

    def mock_prepare(self):
        self.request.state = Request.State.COMPLETED
        self.request.decision = Request.Decision.APPROVED
        self.request.save()

    mocker.patch.object(
        CreateRequest, "_CreateRequest__prepare_request", mock_prepare
    )
    request = __request_service().request
    assert request.name == "test"
    assert request.description == "description"
    assert request.state == "Completed"
    assert request.decision == "Approved"


@pytest.mark.django_db
def test_create_request_not_process(mocker):
    """Test to create a new request without processing"""

    mocker.patch.object(
        CreateRequest, "_CreateRequest__prepare_request", return_value=None
    )
    request = __request_service().request
    assert request.name == "test"
    assert request.description == "description"
    assert request.state == "Pending"
    assert request.decision == "Undecided"


@pytest.mark.django_db
def test_start_request(mocker):
    mocker.patch.object(
        CreateRequest, "_CreateRequest__prepare_request", return_value=None
    )
    send_event = mocker.patch.object(SendEvent, "process")
    service = __request_service()
    service._CreateRequest__start_request()
    assert service.request.state == "Completed"
    assert service.request.decision == "Approved"
    assert send_event.call_count == 2


def __request_service():
    tenant = default_tenant()
    service = CreateRequest(
        {
            "name": "test",
            "description": "description",
            "content": {"param": "val"},
            "tenant": tenant,
        }
    )
    return service.process()
