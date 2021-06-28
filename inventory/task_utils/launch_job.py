""" Task to Launch a Job in Tower and wait for it to end"""
import time
from inventory.task_utils.tower_api import TowerAPI


class LaunchJob:
    """LaunchJob launches a job and waits for it to end"""

    REFRESH_INTERVAL = 10
    JOB_COMPLETION_STATUSES = ("successful", "failed", "error", "canceled")
    # default constructor
    def __init__(self, slug, body):
        self.tower = TowerAPI()
        self.slug = slug
        self.body = body

    # start processing
    def process(self):
        """Send a post request to start the job and wait for it to
        finish by polling the task status using get calls
        """
        attrs = ("id", "url", "artifacts", "status")
        obj = self.tower.post(self.slug, self.body, attrs)
        while obj["status"] not in self.JOB_COMPLETION_STATUSES:
            time.sleep(self.REFRESH_INTERVAL)
            for obj in self.tower.get(obj["url"], attrs):
                pass

        return obj
