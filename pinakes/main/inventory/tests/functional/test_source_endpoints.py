"""Module to test Source end points"""
from unittest.mock import Mock
import json
import pytest
from pinakes.main.inventory.tests.factories import (
    InventoryServicePlanFactory,
    SourceFactory,
    ServiceInventoryFactory,
    ServiceOfferingFactory,
)
from pinakes.main.models import Source


@pytest.mark.django_db
def test_source_list(api_request):
    """Test to list Source endpoint"""

    SourceFactory()
    response = api_request("get", "inventory:source-list")

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 2  # including the default


@pytest.mark.django_db
def test_source_retrieve(api_request):
    """Test to retrieve Source endpoint"""

    last_refresh_stats = {
        "service_inventory": {"adds": 1, "updates": 1, "deletes": 0},
        "service_offering": {"adds": 2, "delates": 0},
        "service_offering_node": {"adds": 3},
        "service_plan": {"adds": 2, "updates": 0},
    }
    source = SourceFactory(
        availability_status="available", last_refresh_stats=last_refresh_stats
    )
    response = api_request("get", "inventory:source-detail", source.id)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == source.id


@pytest.mark.django_db
def test_source_nothing_to_update(api_request):
    """Test to retrieve Source endpoint with no updates"""

    last_refresh_stats = {
        "service_inventory": {"adds": 0, "updates": 0, "deletes": 0},
        "service_offering": {"adds": 0, "delates": 0},
        "service_offering_node": {"adds": 0},
        "service_plan": {"adds": 0, "updates": 0},
    }
    source = SourceFactory(
        availability_status="available", last_refresh_stats=last_refresh_stats
    )
    response = api_request("get", "inventory:source-detail", source.id)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == source.id
    assert content["last_refresh_message"] == "Nothing to update"


@pytest.mark.django_db
def test_source_failed_state(api_request):
    """Test to retrieve Source endpoint in a failed state"""
    source = SourceFactory(
        availability_status="available", refresh_state=Source.State.FAILED
    )
    response = api_request("get", "inventory:source-detail", source.id)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == source.id
    assert "Refresh failed" in content["last_refresh_message"]


@pytest.mark.django_db
def test_source_retrieve_with_error(api_request):
    """Test to retrieve Source endpoint"""

    source = SourceFactory(
        error_code=Source.ErrorCode.SOURCE_CANNOT_BE_CHANGED,
        error_dict={"new_url": "abc", "new_install_uuid": "123"},
        info={"url": "xyz", "install_uuid": "456"},
        availability_status="unavailable",
    )
    response = api_request("get", "inventory:source-detail", source.id)

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["id"] == source.id
    assert (
        content["availability_message"]
        == "Source cannot be changed to url abc uuid 123, \
currently bound to url xyz with uuid 456"
    )


@pytest.mark.django_db
def test_source_refresh(mocker, api_request):
    """Test to refresh Source endpoint"""
    job_id = "uuid1"
    job_mock = Mock(id=job_id)
    job_mock.get_status.return_value = "queued"
    mocker.patch("django_rq.enqueue", return_value=job_mock)

    source = SourceFactory()
    response = api_request("patch", "inventory:source-refresh", source.id)

    assert response.status_code == 202
    assert response.data == {
        "id": job_id,
        "status": "queued",
    }


@pytest.mark.django_db
def test_multiple_source_refreshes(mocker, api_request):
    """Test multiple source refreshes at the same time"""
    job_id = "uuid1"
    job_status = "queued"
    job_mock = Mock(id=job_id)
    job_mock.get_status.return_value = job_status
    mocker.patch("rq.job.Job.fetch", return_value=job_mock)

    source = SourceFactory(last_refresh_task_ref=job_id)
    response = api_request("patch", "inventory:source-refresh", source.id)

    assert response.status_code == 429
    content = json.loads(response.content)
    assert content[
        "detail"
    ] == "Refresh job {} is already {}, please try again later".format(
        job_id, job_status
    )


@pytest.mark.django_db
def test_source_patch(api_request):
    """Test to patch Source endpoint"""

    source = SourceFactory()
    response = api_request(
        "patch",
        "inventory:source-detail",
        source.id,
        {"name": "update"},
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_source_delete_not_supported(api_request):
    """Test to delete Source endpoint"""

    source = SourceFactory()
    response = api_request("delete", "inventory:source-detail", source.id)

    assert response.status_code == 405


@pytest.mark.django_db
def test_source_put_not_supported(api_request):
    """Test to put Source endpoint"""

    source = SourceFactory()
    response = api_request(
        "put",
        "inventory:source-detail",
        source.id,
        {"name": "update"},
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_source_service_inventory_list(api_request):
    """Test to list ServiceInventories by a certain Source endpoint"""

    source1 = SourceFactory()
    source2 = SourceFactory()
    ServiceInventoryFactory(source=source1)
    ServiceInventoryFactory(source=source1)
    service_inventory = ServiceInventoryFactory(source=source2)

    response = api_request(
        "get", "inventory:source-service_inventory-list", source2.id
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1
    assert content["results"][0]["id"] == service_inventory.id


@pytest.mark.django_db
def test_source_service_plan_list(api_request):
    """Test to list ServicePlans by a certain Source endpoint"""

    source1 = SourceFactory()
    source2 = SourceFactory()
    InventoryServicePlanFactory(source=source1)
    InventoryServicePlanFactory(source=source1)
    InventoryServicePlanFactory(source=source2)

    response = api_request(
        "get", "inventory:source-service_plan-list", source1.id
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 2


@pytest.mark.django_db
def test_source_service_offering_list(api_request):
    """Test to list ServiceOfferings by a certain Source endpoint"""

    source1 = SourceFactory()
    source2 = SourceFactory()
    ServiceOfferingFactory(source=source1)
    ServiceOfferingFactory(source=source1)
    ServiceOfferingFactory(source=source2)
    response = api_request(
        "get", "inventory:source-service_offering-list", source2.id
    )

    assert response.status_code == 200
    content = json.loads(response.content)

    assert content["count"] == 1
