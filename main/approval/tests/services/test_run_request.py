"""module to test execute a request"""
import pytest
from main.approval.tests.factories import RequestFactory
from main.approval.services.send_event import SendEvent
from main.approval.services.run_request import RunRequest


@pytest.mark.django_db
def test_start_request(mocker):
    request = RequestFactory()
    send_event = mocker.patch.object(SendEvent, "process")
    RunRequest(request.id).process()
    request.refresh_from_db()
    assert request.state == "Completed"
    assert request.decision == "Approved"
    assert send_event.call_count == 2
