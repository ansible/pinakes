"""module to test updating request"""

import pytest
from ansible_catalog.main.approval.models import Request, Action
from ansible_catalog.main.approval.tests.factories import (
    RequestFactory,
    WorkflowFactory,
)
from ansible_catalog.main.approval.services.update_request import (
    UpdateRequest,
    AUTO_APPROVED_REASON,
)
from ansible_catalog.main.approval.services.send_event import SendEvent


@pytest.mark.django_db
def test_update_single_request(mocker):
    """Test update state of a standalone request"""
    testing_suites = (
        # (options, event, updated_state, extra_attr)
        (
            {"state": Request.State.STARTED},
            SendEvent.EVENT_REQUEST_STARTED,
            Request.State.STARTED,
            None,
        ),
        (
            {"state": Request.State.NOTIFIED},
            None,
            Request.State.NOTIFIED,
            "notified_at",
        ),
        (
            {
                "state": Request.State.COMPLETED,
                "decision": Request.Decision.APPROVED,
            },
            SendEvent.EVENT_REQUEST_FINISHED,
            Request.State.COMPLETED,
            "finished_at",
        ),
        (
            {"state": Request.State.CANCELED},
            SendEvent.EVENT_REQUEST_CANCELED,
            Request.State.CANCELED,
            "finished_at",
        ),
        (
            {
                "state": Request.State.FAILED,
                "decision": Request.Decision.ERROR,
            },
            SendEvent.EVENT_REQUEST_FINISHED,
            Request.State.FAILED,
            "finished_at",
        ),
    )
    for suite in testing_suites:
        event_service = mocker.patch.object(
            SendEvent, "__init__", return_value=None
        )
        mocker.patch.object(SendEvent, "process")
        workflow = WorkflowFactory()
        request = RequestFactory(workflow=workflow)
        request = UpdateRequest(request, suite[0]).process().request

        assert request.state == suite[2]
        if suite[1]:
            event_service.assert_called_once_with(request, suite[1])
        if suite[3]:
            assert getattr(request, suite[3]) is not None


@pytest.mark.django_db
def test_auto_approve(mocker):
    """Test auto approve a request"""
    init_request = RequestFactory(workflow=None)
    mocker.patch.object(SendEvent, "process")
    request = (
        UpdateRequest(init_request, {"state": Request.State.STARTED})
        .process()
        .request
    )

    assert request.state == Request.State.COMPLETED
    assert request.reason == AUTO_APPROVED_REASON
    assert request.decision == Request.Decision.APPROVED


@pytest.mark.django_db
def test_update_child1(mocker):
    """Test updating first child with siblings and parent"""
    testing_suites = (
        # (init_state, options, expect_states)
        (
            Request.State.PENDING,
            {"state": Request.State.STARTED},
            (
                Request.State.STARTED,
                Request.State.STARTED,
                Request.State.PENDING,
            ),
        ),
        (
            Request.State.STARTED,
            {"state": Request.State.NOTIFIED},
            (
                Request.State.NOTIFIED,
                Request.State.NOTIFIED,
                Request.State.PENDING,
            ),
        ),
        (
            Request.State.NOTIFIED,
            {
                "state": Request.State.COMPLETED,
                "decision": Request.Decision.APPROVED,
            },
            (
                Request.State.NOTIFIED,
                Request.State.COMPLETED,
                Request.State.STARTED,
            ),
        ),
        (
            Request.State.NOTIFIED,
            {
                "state": Request.State.COMPLETED,
                "decision": Request.Decision.DENIED,
            },
            (
                Request.State.COMPLETED,
                Request.State.COMPLETED,
                Request.State.SKIPPED,
            ),
        ),
        (
            Request.State.NOTIFIED,
            {
                "state": Request.State.FAILED,
                "decision": Request.Decision.ERROR,
            },
            (
                Request.State.FAILED,
                Request.State.FAILED,
                Request.State.SKIPPED,
            ),
        ),
    )
    for suite in testing_suites:
        mocker.patch.object(SendEvent, "process")
        root = RequestFactory(state=suite[0], number_of_children=2)
        workflow1 = WorkflowFactory(
            group_refs=[{"group_name": "g1", "group_ref": "r1"}]
        )
        child1 = RequestFactory(
            parent=root, state=suite[0], workflow=workflow1
        )
        workflow2 = WorkflowFactory(
            group_refs=[{"group_name": "g2", "group_ref": "r2"}]
        )
        child2 = RequestFactory(parent=root, workflow=workflow2)
        UpdateRequest(child1, suite[1]).process()

        root.refresh_from_db()
        child1.refresh_from_db()
        child2.refresh_from_db()
        assert root.state == suite[2][0]
        assert child1.state == suite[2][1]
        assert child2.state == suite[2][2]


@pytest.mark.django_db
def test_update_child2(mocker):
    """Test updating last child with siblings and parent"""
    testing_suites = (
        # (init_state, options, expect_states)
        (
            Request.State.PENDING,
            {"state": Request.State.STARTED},
            (
                Request.State.NOTIFIED,
                Request.State.COMPLETED,
                Request.State.STARTED,
            ),
        ),
        (
            Request.State.STARTED,
            {"state": Request.State.NOTIFIED},
            (
                Request.State.NOTIFIED,
                Request.State.COMPLETED,
                Request.State.NOTIFIED,
            ),
        ),
        (
            Request.State.NOTIFIED,
            {
                "state": Request.State.COMPLETED,
                "decision": Request.Decision.APPROVED,
            },
            (
                Request.State.COMPLETED,
                Request.State.COMPLETED,
                Request.State.COMPLETED,
            ),
        ),
        (
            Request.State.NOTIFIED,
            {
                "state": Request.State.COMPLETED,
                "decision": Request.Decision.DENIED,
            },
            (
                Request.State.COMPLETED,
                Request.State.COMPLETED,
                Request.State.COMPLETED,
            ),
        ),
        (
            Request.State.NOTIFIED,
            {
                "state": Request.State.FAILED,
                "decision": Request.Decision.ERROR,
            },
            (
                Request.State.FAILED,
                Request.State.COMPLETED,
                Request.State.FAILED,
            ),
        ),
    )
    for suite in testing_suites:
        mocker.patch.object(SendEvent, "process")
        root = RequestFactory(
            state=Request.State.NOTIFIED, number_of_children=2
        )
        workflow1 = WorkflowFactory(
            group_refs=[{"group_name": "g1", "group_ref": "r1"}]
        )
        child1 = RequestFactory(
            parent=root,
            state=Request.State.COMPLETED,
            decision=Request.Decision.APPROVED,
            workflow=workflow1,
        )
        workflow2 = WorkflowFactory(
            group_refs=[{"group_name": "g1", "group_ref": "r1"}]
        )
        child2 = RequestFactory(
            parent=root, state=suite[0], workflow=workflow2
        )
        UpdateRequest(child2, suite[1]).process()

        root.refresh_from_db()
        child1.refresh_from_db()
        child2.refresh_from_db()
        assert root.state == suite[2][0]
        assert child1.state == suite[2][1]
        assert child2.state == suite[2][2]


@pytest.mark.django_db
def test_cancel_root(mocker):
    """Test canceling root with children"""
    event_service = mocker.patch.object(
        SendEvent, "__init__", return_value=None
    )
    mocker.patch.object(SendEvent, "process")
    root = RequestFactory(state=Request.State.NOTIFIED, number_of_children=2)
    child1 = RequestFactory(parent=root, state=Request.State.NOTIFIED)
    child2 = RequestFactory(parent=root)
    UpdateRequest(root, {"state": Request.State.CANCELED}).process()

    root.refresh_from_db()
    child1.refresh_from_db()
    child2.refresh_from_db()
    assert root.state == Request.State.CANCELED
    assert child1.state == Request.State.NOTIFIED
    assert child2.state == Request.State.SKIPPED

    event_service.assert_called_once_with(
        root, SendEvent.EVENT_REQUEST_CANCELED
    )


@pytest.mark.django_db
def test_complete_canceled():
    """Test completing a child of cancled request"""
    root = RequestFactory(state=Request.State.CANCELED, number_of_children=2)
    child1 = RequestFactory(parent=root, state=Request.State.NOTIFIED)
    child2 = RequestFactory(parent=root, state=Request.State.SKIPPED)
    UpdateRequest(
        child1,
        {
            "state": Request.State.COMPLETED,
            "decision": Request.Decision.APPROVED,
        },
    ).process()

    root.refresh_from_db()
    child1.refresh_from_db()
    child2.refresh_from_db()
    assert root.state == Request.State.CANCELED
    assert child1.state == Request.State.COMPLETED
    assert child1.decision == Request.Decision.APPROVED
    assert child2.state == Request.State.SKIPPED


@pytest.mark.django_db
def test_update_parallel():
    """Test update a child in parallel group"""
    testing_suites = (
        # (child2_initial_state, child2_init_decision, expect_states)
        (
            Request.State.NOTIFIED,
            Request.Decision.UNDECIDED,
            (
                Request.State.COMPLETED,
                Request.State.NOTIFIED,
                Request.State.PENDING,
                Request.State.PENDING,
            ),
        ),
        (
            Request.State.COMPLETED,
            Request.Decision.APPROVED,
            (
                Request.State.COMPLETED,
                Request.State.COMPLETED,
                Request.State.STARTED,
                Request.State.STARTED,
            ),
        ),
    )
    for suite in testing_suites:
        root = RequestFactory(
            state=Request.State.NOTIFIED, number_of_children=4
        )
        workflow1 = WorkflowFactory(
            group_refs=[{"group_name": "g1", "group_ref": "r1"}]
        )
        child1 = RequestFactory(
            parent=root, state=Request.State.NOTIFIED, workflow=workflow1
        )
        child2 = RequestFactory(
            parent=root, state=suite[0], decision=suite[1], workflow=workflow1
        )

        workflow2 = WorkflowFactory(
            group_refs=[{"group_name": "g2", "group_ref": "r2"}]
        )
        child3 = RequestFactory(parent=root, workflow=workflow2)
        child4 = RequestFactory(parent=root, workflow=workflow2)

        UpdateRequest(
            child1,
            {
                "state": Request.State.COMPLETED,
                "decision": Request.Decision.APPROVED,
            },
        ).process()

        root.refresh_from_db()
        child1.refresh_from_db()
        child2.refresh_from_db()
        child3.refresh_from_db()
        child4.refresh_from_db()
        assert child1.state == suite[2][0]
        assert child2.state == suite[2][1]
        assert child3.state == suite[2][2]
        assert child4.state == suite[2][3]
