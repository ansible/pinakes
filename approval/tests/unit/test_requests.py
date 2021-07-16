import pytest

from approval.tests.factories import (
    TenantFactory,
    RequestFactory,
)
from approval.models import Request

class TestRequest:
    @pytest.mark.django_db
    def test_request(self):
        request = RequestFactory()
        assert request.state == Request.State.PENDING
        assert request.decision == Request.Decision.UNDECIDED
