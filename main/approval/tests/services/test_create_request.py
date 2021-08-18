""" Module to test creating requests """
import pytest
import django_rq
from main.tests.factories import default_tenant
from main.approval.tests.factories import RequestFactory
from main.approval.services.create_request import CreateRequest
from main.approval.models import Request
from main.models import Tenant
from main.approval.services.send_event import SendEvent


@pytest.mark.django_db
def test_create_request_not_process(mocker):
    """Test to create a new request"""

    tenant = default_tenant()
    service = CreateRequest(
        {
            "name": "test",
            "description": "description",
            "content": {"param": "val"},
            "tenant": tenant,
        }
    )
    mocker.patch("django_rq.enqueue")
    request = service.process().request
    assert request.name == "test"
    assert request.description == "description"
    assert request.state == "Pending"
    assert request.decision == "Undecided"
