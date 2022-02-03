""" Test module for ControllerConfig  """
from unittest.mock import Mock
import pytest

from ansible_catalog.main.inventory.task_utils.controller_config import (
    ControllerConfig,
)


class TestControllerConfig:
    """Test class for ControllerConfig."""

    def fake_config(self, *_args, **_kwargs):
        """Create a fake response object"""
        objs = [
            {
                "time_zone": "UTC",
                "version": "4.1.0",
                "analytics_status": "off",
            }
        ]

        for i in objs:
            yield i

    def test_controller_config(self):
        """Test fetching controller config"""
        tower_mock = Mock()
        cc = ControllerConfig(tower_mock)
        tower_mock.get.side_effect = self.fake_config
        import pdb

        pdb.set_trace()
        response = cc.process()

        assert (response["version"]) == "4.1.0"
