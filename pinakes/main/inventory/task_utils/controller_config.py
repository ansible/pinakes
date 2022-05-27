"""Get Controller Config Information"""
import logging

logger = logging.getLogger("inventory")


class ControllerConfig:
    """ControllerConfig fetch controllers version"""

    def __init__(self, tower):
        self.tower = tower
        self.tower_info = None

    def process(self):
        logger.debug("fetching /api/v2/ping/")
        for data in self.tower.get(
            "/api/v2/ping/", ["version", "install_uuid"]
        ):
            self.tower_info = data
            logger.debug(data)

        return self
