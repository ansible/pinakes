""" Get Controller Config Information
"""
import dateutil.parser


class ControllerConfig:
    """ControllerConfig fetch controllers version"""

    def __init__(self, tower):
        self.tower = tower

    def process(self):
        for data in self.tower.get("/api/v2/config", ("version")):
            return data
