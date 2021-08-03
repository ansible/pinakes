""" Test module for starting a TowerJob given a service offering with params """
from unittest.mock import patch, Mock
import pytest
from main.inventory.tests.factories import ServiceOfferingFactory, OfferingKind
from main.inventory.services.start_tower_job import StartTowerJob


@patch("main.inventory.services.start_tower_job.django_rq.enqueue", autoSpec=True)
@pytest.mark.django_db
def test_starting_a_workflow(mock):
    """Test launching a workflow"""
    job_id = "Charkie"
    service_offering = ServiceOfferingFactory(kind=OfferingKind.WORKFLOW)

    mock.return_value = Mock(id=job_id)
    params = {"service_parameters": "abc"}
    assert StartTowerJob(service_offering.id, params).process() == job_id
    assert (mock.call_count) == 1


@patch("main.inventory.services.start_tower_job.django_rq.enqueue", autoSpec=True)
@pytest.mark.django_db
def test_starting_a_job_template(mock):
    """Test launching a job template"""
    job_id = "Hundley"
    service_offering = ServiceOfferingFactory(kind=OfferingKind.JOB_TEMPLATE)

    mock.return_value = Mock(id=job_id)
    params = {"service_parameters": "abc"}
    assert StartTowerJob(service_offering.id, params).process() == job_id
    assert (mock.call_count) == 1
