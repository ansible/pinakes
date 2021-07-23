""" Background tasks for inventory """
from main.inventory.task_utils.refresh_inventory import RefreshInventory
from main.inventory.task_utils.launch_job import LaunchJob

def refresh_task(tenant_id, source_id):
    """Run the Refresh task"""
    obj = RefreshInventory(tenant_id, source_id)
    return obj.process()


def launch_tower_task(slug, body):
    """Launch a job on the tower"""
    print("Launching job")
    obj = LaunchJob(slug, body).process()
    print(obj)
    print("finished")
