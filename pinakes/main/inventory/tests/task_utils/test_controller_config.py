"""Test module for ControllerConfig"""
from unittest.mock import Mock

from pinakes.main.inventory.task_utils.controller_config import (
    ControllerConfig,
)


class TestControllerConfig:
    """Test class for ControllerConfig."""

    def test_controller_config(self):
        """Test fetching controller config"""
        config = [
            {
                "time_zone": "UTC",
                "version": "4.1.0",
                "analytics_status": "off",
                "install_uuid": "abcdef12-3456-7890-ad10-1234567890ab",
            }
        ]
        tower_mock = Mock()
        tower_mock.get.return_value = config

        svc = ControllerConfig(tower_mock).process()
        response = svc.tower_info

        assert (response["version"]) == "4.1.0"
