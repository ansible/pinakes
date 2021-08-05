""" Module to Test Launching of Job """
from unittest.mock import patch
from main.inventory.task_utils.launch_job import LaunchJob


class TestLaunchJob:
    """Test Launch of Job"""

    @patch("time.sleep", return_value=None)
    @patch("main.inventory.task_utils.launch_job.TowerAPI", autoSpec=True)
    def test_process(self, mock1, mock2):
        """Test the process method"""
        instance = mock1.return_value
        instance.post.return_value = {"status": "pending", "url": "/abc/def/"}

        def result(*_args, **_kwargs):
            yield {"status": "failed", "url": "/abc/def/"}

        instance.get.side_effect = result
        launch_job = LaunchJob("/abc/def/", {"name": "Fred"})
        obj = launch_job.process()
        assert (obj["status"]) == "failed"
