""" Module to test creating requests """
import pytest
from main.tests.factories import default_tenant
from main.approval.services.create_request import CreateRequest


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
