""" Get Controller Config Information
"""


class ControllerConfig:
    """ControllerConfig fetch controllers version"""

    def __init__(self, tower):
        self.tower = tower
        self.tower_info = None

    def process(self):
        for data in self.tower.get("/api/v2/config", ["version"]):
            self.tower_info = data

        return self
