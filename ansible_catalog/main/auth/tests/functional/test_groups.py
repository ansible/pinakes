import uuid

import pytest

from ansible_catalog.main.auth.tests import factories


@pytest.mark.django_db
def test_groups_list(api_request):
    group = factories.GroupFactory()
    response = api_request("get", "group-list")

    assert response.status_code == 200
    assert response.data["count"] == 1

    result = response.data["results"][0]
    assert result == {"id": group.id, "name": group.name, "parent_id": None}


@pytest.mark.django_db
def test_groups_retrieve(api_request):
    group = factories.GroupFactory()
    response = api_request("get", "group-detail", group.id)

    assert response.status_code == 200
    assert response.data == {
        "id": group.id,
        "name": group.name,
        "parent_id": None,
    }


@pytest.mark.django_db
def test_groups_retrieve_nonexist(api_request):
    response = api_request("get", "group-detail", str(uuid.uuid4()))

    assert response.status_code == 404
