import pytest

from main.tests.factories import TenantFactory
from main.approval.tests.factories import RequestFactory

from main.approval.models import Request


class TestRequest:
    @pytest.mark.django_db
    def test_request(self):
        request = RequestFactory()
        assert request.state == Request.State.PENDING
        assert request.decision == Request.Decision.UNDECIDED
