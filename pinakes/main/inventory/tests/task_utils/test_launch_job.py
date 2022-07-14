"""Module to Test Launching of Job"""
from unittest.mock import patch
import pytest
from pinakes.main.inventory.task_utils.launch_job import (
    LaunchJob,
)

from pinakes.main.inventory.models import (
    ServiceInstance,
)
from pinakes.main.inventory.tests.factories import (
    InventoryServicePlanFactory,
    ServiceOfferingFactory,
)


class TestLaunchJob:
    """Test Launch of Job"""

    @patch("time.sleep", return_value=None)
    @patch(
        "pinakes.main.inventory.task_utils.launch_job.TowerAPI",
        autoSpec=True,
    )
    def test_process_with_failed_status(self, mock1, _mock2):
        """Test the process method"""
        instance = mock1.return_value
        instance.post.return_value = {
            "id": 123,
            "status": "pending",
            "url": "/abc/def/",
        }

        def result(*_args, **_kwargs):
            yield {"id": 123, "status": "failed", "url": "/abc/def/"}

        instance.get.side_effect = result
        launch_job = LaunchJob("/abc/def/", {"name": "Fred"})
        with pytest.raises(RuntimeError, match=r"Job 123 has failed status"):
            launch_job.process()

    @patch("time.sleep", return_value=None)
    @patch(
        "pinakes.main.inventory.task_utils.launch_job.TowerAPI",
        autoSpec=True,
    )
    @pytest.mark.django_db
    def test_process_with_success_status(self, mock1, _mock2):
        """Test the process method"""
        source_ref = "abc"
        service_offering = ServiceOfferingFactory(source_ref=source_ref)
        service_plan = InventoryServicePlanFactory(
            service_offering=service_offering
        )

        instance = mock1.return_value
        instance.post.return_value = {"status": "pending", "url": "/abc/def/"}

        def result(*_args, **_kwargs):
            yield {
                "id": "123",
                "name": "job_name",
                "status": "successful",
                "unified_job_template": source_ref,
                "url": "/abc/def/",
            }

        instance.get.side_effect = result

        launch_job = LaunchJob("/abc/def/", {"name": "Fred"})
        obj = launch_job.process().output
        assert (obj["status"]) == "successful"
        assert ServiceInstance.objects.count() == 1

        service_instance = ServiceInstance.objects.first()
        assert service_instance.tenant == service_offering.tenant
        assert service_instance.source == service_offering.source
        assert service_instance.service_offering == service_offering
        assert service_instance.service_plan == service_plan
        assert service_instance.external_url == "/abc/def/"
