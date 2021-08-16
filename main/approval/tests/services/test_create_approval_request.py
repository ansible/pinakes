""" Test on CreateApprovalRequest service """
import pytest

from main.models import Tenant
from main.approval.models import Request, RequestContext
from main.approval.services.create_approval_request import (
    CreateApprovalRequest,
)


@pytest.mark.django_db
def test_create_approval_request():
    """Test on creating ApprovalRequest service"""

    request_body = {
        "name": "request_1",
        "content": {"a": "b"},
        "tag_resources": [],
        "tenant_id": Tenant.current().id,
    }

    svc = CreateApprovalRequest(request_body)
    svc.process()

    assert Request.objects.count() == 1
    assert RequestContext.objects.count() == 1
