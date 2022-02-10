import uuid
from unittest import mock

import rq.job as rq_job

import pytest


@pytest.mark.django_db
def test_group_sync_start(api_request, mocker):
    job_id = str(uuid.uuid4())
    job_mock = mock.Mock(id=job_id)
    job_mock.get_status.return_value = "queued"
    mocker.patch("django_rq.enqueue", return_value=job_mock)

    response = api_request("post", "group-sync-list")
    assert response.status_code == 202
    assert response.data == {
        "id": job_id,
        "status": "queued",
    }


@pytest.mark.django_db
def test_group_sync_job_status(api_request, mocker):
    mocker.patch("django_rq.get_connection")

    job_id = str(uuid.uuid4())
    job_mock = mock.Mock(id=job_id)
    job_mock.get_status.return_value = "finished"
    mocker.patch.object(rq_job.Job, "fetch", return_value=job_mock)

    response = api_request("get", "task-detail", job_id)

    assert response.status_code == 200
    assert response.data == {
        "id": job_id,
        "status": "finished",
    }


@pytest.mark.django_db
def test_group_sync_missing_job_status(api_request, mocker):
    mocker.patch("django_rq.get_connection")

    job_id = str(uuid.uuid4())
    job_mock = mock.Mock(id=job_id)
    job_mock.get_status.return_value = "finished"
    mocker.patch.object(rq_job.Job, "fetch", side_effect=rq_job.NoSuchJobError)

    response = api_request("get", "task-detail", job_id)

    assert response.status_code == 404
