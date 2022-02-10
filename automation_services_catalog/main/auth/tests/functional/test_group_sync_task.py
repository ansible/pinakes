from datetime import datetime, timedelta
from unittest import mock

from django.conf import settings
from django.utils import timezone as django_tz
import pytest

from automation_services_catalog.common.auth.keycloak import (
    models as keycloak_models,
)
from automation_services_catalog.main.auth import models
from automation_services_catalog.main.auth import tasks
from automation_services_catalog.main.auth.tests import factories


@pytest.mark.django_db
def test_group_sync_task_initial(mocker):
    mocker.patch("rq.get_current_job", return_value=mock.Mock(id="123"))
    mock_client = mock.Mock()
    mocker.patch(
        "automation_services_catalog.common.auth.keycloak_django.get_admin_client",
        return_value=mock_client,
    )

    prev_sync_time = django_tz.now() - timedelta(hours=1)

    to_delete, to_keep, to_update = factories.GroupFactory.create_batch(
        3, last_sync_time=prev_sync_time
    )

    role = factories.RoleFactory(name="arbitrator")
    to_keep.roles.add(role)
    to_update.roles.add(role)
    actual_roles = ["approver", "adjuster"]
    roles = {settings.KEYCLOAK_CLIENT_ID: actual_roles}
    keycloak_groups = [
        keycloak_models.Group(
            id=to_keep.id,
            name=to_keep.name,
            path=to_keep.path,
            sub_groups=[],
            client_roles=roles,
        ),
        keycloak_models.Group(
            id=to_update.id,
            name=to_update.name + "-upd",
            path=to_update.path + "-upd",
            sub_groups=[],
        ),
    ]
    mock_client.list_groups.return_value = keycloak_groups

    tasks.sync_external_groups()

    assert not models.Group.objects.filter(id=to_delete.id).exists()

    group = models.Group.objects.filter(id=to_keep.id).first()
    assert group is not None
    assert group.name == to_keep.name
    assert group.path == to_keep.path
    assert group.last_sync_time != prev_sync_time
    roles = [role.name for role in group.roles.all()]
    assert sorted(roles) == sorted(actual_roles)

    group = models.Group.objects.filter(id=to_update.id).first()
    assert group is not None
    assert group.name == to_update.name + "-upd"
    assert group.path == to_update.path + "-upd"
    assert group.last_sync_time != prev_sync_time
    assert len(group.roles.all()) == 0
