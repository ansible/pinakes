import uuid

import pytest

from automation_services_catalog.main.common.tests import factories


@pytest.mark.django_db
def test_groups_list(api_request):
    group = factories.GroupFactory()
    response = api_request("get", "common:group-list")

    assert response.status_code == 200
    assert response.data["count"] == 1

    result = response.data["results"][0]
    assert result == {"id": group.id, "name": group.name, "parent_id": None}


@pytest.mark.django_db
def test_groups_list_with_roles(api_request):
    group1 = factories.GroupFactory()
    factories.GroupFactory()
    role1 = factories.RoleFactory(name="approver")
    role2 = factories.RoleFactory(name="adjuster")
    group1.roles.add(role1, role2)
    response = api_request(
        "get", "common:group-list", data={"role": "approver"}
    )

    assert response.status_code == 200
    assert response.data["count"] == 1

    result = response.data["results"][0]
    assert result == {"id": group1.id, "name": group1.name, "parent_id": None}


@pytest.mark.django_db
def test_groups_retrieve(api_request):
    group = factories.GroupFactory()
    response = api_request("get", "common:group-detail", group.id)

    assert response.status_code == 200
    assert response.data == {
        "id": group.id,
        "name": group.name,
        "parent_id": None,
    }


@pytest.mark.django_db
def test_groups_retrieve_nonexist(api_request):
    response = api_request("get", "common:group-detail", str(uuid.uuid4()))

    assert response.status_code == 404
