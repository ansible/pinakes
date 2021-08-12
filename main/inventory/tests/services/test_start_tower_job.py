""" Test module for starting a TowerJob given a service offering with params """
from unittest.mock import patch, Mock
import pytest
from main.inventory.tests.factories import ServiceOfferingFactory, OfferingKind
from main.inventory.services.start_tower_job import StartTowerJob


@patch(
    "main.inventory.services.start_tower_job.django_rq.enqueue", autoSpec=True
)
@pytest.mark.django_db
def test_starting_a_workflow(mock):
    """Test launching a workflow"""
    job_id = "Charkie"
    service_offering = ServiceOfferingFactory(
        kind=OfferingKind.WORKFLOW, source_ref=99
    )

    mock.return_value = Mock(id=job_id)
    params = {"service_parameters": "abc"}
    obj = StartTowerJob(service_offering.id, params).process()
    assert obj.job_id() == job_id

    assert (mock.call_count) == 1
    assert (
        mock.call_args.args[1]
        == f"/api/v2/workflows/{service_offering.source_ref}/launch/"
    )
    assert mock.call_args.args[2] == {"extra_vars": "abc"}


@patch(
    "main.inventory.services.start_tower_job.django_rq.enqueue", autoSpec=True
)
@pytest.mark.django_db
def test_starting_a_job_template(mock):
    """Test launching a job template"""
    job_id = "Hundley"
    service_offering = ServiceOfferingFactory(
        kind=OfferingKind.JOB_TEMPLATE, source_ref=98
    )

    mock.return_value = Mock(id=job_id)
    params = {"service_parameters": "xyz"}
    obj = StartTowerJob(service_offering.id, params).process()
    assert obj.job_id() == job_id
    assert (mock.call_count) == 1
    assert (
        mock.call_args.args[1]
        == f"/api/v2/job_templates/{service_offering.source_ref}/launch/"
    )
    assert mock.call_args.args[2] == {"extra_vars": "xyz"}
