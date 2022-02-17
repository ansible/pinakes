"""module to test creating actions"""

import pytest

from pinakes.main.approval.models import Request, Action
from pinakes.main.approval.services.create_action import (
    CreateAction,
)
from pinakes.main.approval.tests.factories import (
    RequestFactory,
)
from pinakes.main.approval.services.update_request import (
    UpdateRequest,
)
from pinakes.main.approval.exceptions import (
    InvalidStateTransitionException,
    BlankParameterException,
)


@pytest.mark.django_db
def test_create_memo_action():
    """Test memo action"""
    request = RequestFactory()
    CreateAction(
        request, {"operation": Action.Operation.MEMO, "comments": "something"}
    ).process()

    request.refresh_from_db()
    action = request.actions.first()
    assert action.operation == Action.Operation.MEMO
    assert action.comments == "something"


@pytest.mark.django_db
def test_create_action_normal(mocker):
    """Test normal actions"""
    testing_suites = (
        # (request_init_state, operation, comments, updates)
        (
            Request.State.PENDING,
            Action.Operation.START,
            "",
            {"state": Request.State.STARTED},
        ),
        (
            Request.State.STARTED,
            Action.Operation.NOTIFY,
            "",
            {"state": Request.State.NOTIFIED},
        ),
        (
            Request.State.PENDING,
            Action.Operation.SKIP,
            "",
            {"state": Request.State.SKIPPED},
        ),
        (
            Request.State.NOTIFIED,
            Action.Operation.APPROVE,
            "",
            {
                "state": Request.State.COMPLETED,
                "decision": Request.Decision.APPROVED,
                "reason": "",
            },
        ),
        (
            Request.State.NOTIFIED,
            Action.Operation.DENY,
            "regret",
            {
                "state": Request.State.COMPLETED,
                "decision": Request.Decision.DENIED,
                "reason": "regret",
            },
        ),
        (
            Request.State.PENDING,
            Action.Operation.CANCEL,
            "",
            {
                "state": Request.State.CANCELED,
                "decision": Request.Decision.CANCELED,
                "reason": "",
            },
        ),
        (
            Request.State.NOTIFIED,
            Action.Operation.ERROR,
            "unexpected",
            {
                "state": Request.State.FAILED,
                "decision": Request.Decision.ERROR,
                "reason": "unexpected",
            },
        ),
    )

    for suite in testing_suites:
        request = RequestFactory(state=suite[0])
        update_service = mocker.patch.object(
            UpdateRequest, "__init__", return_value=None
        )
        mocker.patch.object(UpdateRequest, "process")
        CreateAction(
            request, {"operation": suite[1], "comments": suite[2]}
        ).process()

        action = request.actions.first()
        assert action.operation == suite[1]
        update_service.assert_called_once_with(request, suite[3])


@pytest.mark.django_db
def test_create_action_abnormal():
    """Test actions with exception"""
    testing_suites = (
        # (request_init_state, operation, comments, exception)
        (
            Request.State.STARTED,
            Action.Operation.MEMO,
            "",
            BlankParameterException,
        ),
        (
            Request.State.COMPLETED,
            Action.Operation.START,
            "",
            InvalidStateTransitionException,
        ),
        (
            Request.State.PENDING,
            Action.Operation.NOTIFY,
            "",
            InvalidStateTransitionException,
        ),
        (
            Request.State.NOTIFIED,
            Action.Operation.SKIP,
            "",
            InvalidStateTransitionException,
        ),
        (
            Request.State.SKIPPED,
            Action.Operation.APPROVE,
            "",
            InvalidStateTransitionException,
        ),
        (
            Request.State.CANCELED,
            Action.Operation.DENY,
            "regret",
            InvalidStateTransitionException,
        ),
        (
            Request.State.NOTIFIED,
            Action.Operation.DENY,
            "",
            BlankParameterException,
        ),
        (
            Request.State.SKIPPED,
            Action.Operation.CANCEL,
            "",
            InvalidStateTransitionException,
        ),
        (
            Request.State.NOTIFIED,
            Action.Operation.ERROR,
            "",
            BlankParameterException,
        ),
        (
            Request.State.COMPLETED,
            Action.Operation.ERROR,
            "unexpected",
            InvalidStateTransitionException,
        ),
    )

    for suite in testing_suites:
        request = RequestFactory(state=suite[0])
        with pytest.raises(suite[3]):
            CreateAction(
                request, {"operation": suite[1], "comments": suite[2]}
            ).process()


@pytest.mark.django_db
def test_action_only_on_leaf():
    """Test actions that must be on leaf node"""
    for operation in (
        Action.Operation.APPROVE,
        Action.Operation.DENY,
        Action.Operation.ERROR,
    ):
        request = RequestFactory(state=Request.State.NOTIFIED)
        request.create_child()
        with pytest.raises(InvalidStateTransitionException):
            CreateAction(
                request, {"operation": operation, "comments": "word"}
            ).process()


@pytest.mark.django_db
def test_action_only_on_root():
    """Test actions that must be on root node"""
    request = RequestFactory()
    child = request.create_child()
    with pytest.raises(InvalidStateTransitionException):
        CreateAction(child, {"operation": Action.Operation.CANCEL}).process()
