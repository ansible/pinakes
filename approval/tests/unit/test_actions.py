import pytest

from approval.tests.factories import (
    TenantFactory,
    ActionFactory,
)
from approval.models import Action

class TestAction:
    @pytest.mark.django_db
    def test_action(self):
        action = ActionFactory()
        assert action.operation == Action.Operation.Memo

    @pytest.mark.django_db
    def test_action_operation(self):
        action = ActionFactory(operation="bad")
        assert action.operation == "bad" # TODO: why allow any string?
