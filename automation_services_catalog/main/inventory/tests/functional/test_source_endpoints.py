""" Module to test Source end points """
from unittest.mock import Mock
import json
import pytest
from automation_services_catalog.main.inventory.tests.factories import (
    InventoryServicePlanFactory,
    SourceFactory,
    ServiceInventoryFactory,
    ServiceOfferingFactory,
)


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

    source = SourceFactory()
    response = api_request("get", "inventory:source-detail", source.id)

    assert response.status_code == 200
    content = json.loads(response.content)
    assert content["id"] == source.id


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
