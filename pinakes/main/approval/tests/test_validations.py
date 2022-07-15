"""Test validation methods"""
import pytest
from pinakes.main.approval import validations
from pinakes.main.common.tests.factories import (
    GroupFactory,
    RoleFactory,
)
from pinakes.main.approval.tests.factories import (
    WorkflowFactory,
    RequestFactory,
)
from pinakes.main.approval.exceptions import (
    DuplicatedUuidException,
    GroupNotExistException,
    NoAppoverRoleException,
    WorkflowInUseException,
    WorkflowIsLinkedException,
)
from pinakes.main.catalog.services.handle_approval_events import (
    HandleApprovalEvents,
)
from pinakes.main.approval.tests.services.test_link_workflow import (
    create_and_link,
)


@pytest.mark.django_db
def test_validate_approval_groups():
    """Validate approval groups for normal case"""

    group = GroupFactory()
    role1 = RoleFactory(name="approval-approver")
    group.roles.add(role1)
    group_refs = [{"name": group.name, "uuid": group.id}]

    result = validations.validate_approver_groups(group_refs, True)
    assert group_refs == result

    role2 = RoleFactory(name="approval-admin")
    group.roles.remove(role1)
    group.roles.add(role2)

    result = validations.validate_approver_groups(group_refs, False)
    assert group_refs == result


@pytest.mark.django_db
def test_validate_approval_groups_dup_groups():
    """Validate approval groups when duplicate groups are input"""

    group = GroupFactory()
    role1 = RoleFactory(name="approval-approver")
    group.roles.add(role1)
    group_refs = [
        {"name": group.name, "uuid": group.id},
        {"name": group.name, "uuid": group.id},
    ]

    with pytest.raises(DuplicatedUuidException):
        validations.validate_approver_groups(group_refs, True)


@pytest.mark.django_db
def test_validate_approval_group_not_exist():
    """Validate a non-existing group"""

    group_refs = [{"name": "mygroup", "uuid": "uuid1"}]

    with pytest.raises(GroupNotExistException):
        validations.validate_approver_groups(group_refs, True)

    results = validations.validate_approver_groups(group_refs, False)
    assert results[0]["name"] == "mygroup (Group does not exist)"


@pytest.mark.django_db
def test_validate_approval_group_no_role():
    """Validate a group having no approver role"""

    group = GroupFactory()
    role1 = RoleFactory(name="non-approval-approver")
    group.roles.add(role1)
    group_refs = [{"name": group.name, "uuid": group.id}]

    with pytest.raises(NoAppoverRoleException):
        validations.validate_approver_groups(group_refs)

    results = validations.validate_approver_groups(group_refs, False)
    assert results[0]["name"] == f"{group.name} (No approver role)"


@pytest.mark.django_db
def test_validate_workflow(mocker):
    """Validate a workflow with approver groups"""

    workflow = WorkflowFactory()
    group_refs = [{"name": "some name", "uuid": "some-uuid"}]
    mocker.patch(
        "pinakes.main.approval.validations.validate_approver_groups",
        return_value=group_refs,
    )
    validations.validate_and_update_approver_groups(workflow)
    assert workflow.group_refs == group_refs


@pytest.mark.django_db
def test_validate_runtime_no_group():
    """Validate a request with no group"""

    request = RequestFactory()
    assert validations.runtime_validate_group(request) is True


@pytest.mark.django_db
def test_validate_runtime_group_not_exist(mocker):
    """Validate a request with a non-existing group"""

    mocker.patch.object(HandleApprovalEvents, "process", return_value=None)
    request = RequestFactory(group_ref="nonexist")
    assert validations.runtime_validate_group(request) is False
    request.refresh_from_db()
    assert request.state == "failed"


@pytest.mark.django_db
def test_validate_runtime_group_with_role():
    """Validate a request with a group having a right approver role"""

    group = GroupFactory()
    role1 = RoleFactory(name="approval-approver")
    group.roles.add(role1)
    request = RequestFactory(group_ref=group.id)
    assert validations.runtime_validate_group(request) is True


@pytest.mark.django_db
def test_validate_runtime_group_without_role(mocker):
    """Validate a request with a group having no approver roles"""

    mocker.patch.object(HandleApprovalEvents, "process", return_value=None)
    group = GroupFactory()
    role1 = RoleFactory(name="non-approval-approver")
    group.roles.add(role1)
    request = RequestFactory(group_ref=group.id)
    assert validations.runtime_validate_group(request) is False
    request.refresh_from_db()
    assert request.state == "failed"


@pytest.mark.django_db
def test_validate_linked_workflow_not_deletable():
    """workflows that have taglink associations cannot be deleted"""
    workflow, _portfolio, _resource_obj = create_and_link()
    with pytest.raises(WorkflowIsLinkedException):
        validations.validate_workflow_deletable(workflow)


@pytest.mark.django_db
def test_validate_in_use_workflow_not_deletable():
    """workflows that are in use cannot be deleted"""
    workflow = WorkflowFactory()
    RequestFactory(workflow=workflow, state="started")
    with pytest.raises(WorkflowInUseException):
        validations.validate_workflow_deletable(workflow)


@pytest.mark.django_db
def test_validate_workflow_deletable():
    """workflows that are in use cannot be deleted"""
    workflow = WorkflowFactory()
    RequestFactory(workflow=workflow, state="skipped")
    validations.validate_workflow_deletable(workflow)
