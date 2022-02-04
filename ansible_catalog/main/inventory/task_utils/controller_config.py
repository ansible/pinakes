""" Get Controller Config Information
"""


class ControllerConfig:
    """ControllerConfig fetch controllers version"""

    def __init__(self, tower):
        self.tower = tower

    def process(self):
        """Get the Controller Config Information as a dict"""
        for data in self.tower.get("/api/v2/config", ("version")):
            return data
