import pytest

from automation_services_catalog.main.approval.tests.factories import RequestFactory

from automation_services_catalog.main.approval.models import Request


@pytest.mark.django_db
def test_request_standalone():
    """Test a single request"""
    request = RequestFactory()
    assert request.state == Request.State.PENDING
    assert request.decision == Request.Decision.UNDECIDED

    request.invalidate_number_of_children()
    request.invalidate_number_of_finished_children()
    assert request.number_of_children == 0
    assert request.number_of_finished_children == 0

    assert request.is_root() is True
    assert request.is_leaf() is True
    assert request.is_parent() is False
    assert request.is_child() is False


@pytest.mark.django_db
def test_request_multiple():
    """Test request with children"""
    parent = RequestFactory(name="test1", description="desc1")
    child1 = parent.create_child()
    child2 = parent.create_child()
    child3 = parent.create_child()

    assert child1.state == Request.State.PENDING
    assert child1.decision == Request.Decision.UNDECIDED

    assert parent.is_root() is True
    assert parent.is_leaf() is False
    assert parent.is_parent() is True
    assert parent.is_child() is False
    assert parent.has_finished() is False
    assert child3.is_root() is False
    assert child3.is_leaf() is True
    assert child3.is_parent() is False
    assert child3.is_child() is True
    assert child3.has_finished() is False

    assert parent.root() == parent
    assert child1.root() == parent

    assert parent.name == child2.name
    assert parent.description == child2.description

    parent.invalidate_number_of_finished_children()
    assert parent.number_of_children == 3
    assert parent.number_of_finished_children == 0

    child2.state = Request.State.SKIPPED
    child2.save()
    parent.invalidate_number_of_finished_children()
    assert child2.has_finished() is True
    assert parent.number_of_finished_children == 1
