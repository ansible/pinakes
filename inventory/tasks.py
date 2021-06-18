""" Module to import objects from Automation Controller to
    Catalog Inventory.
"""
from ansible_catalog.celery import app
from django.conf import settings
from inventory.task_utils.refresh_inventory import RefreshInventory
from inventory.task_utils.launch_job import LaunchJob


@app.task
def import_tower_objects(tenant_id, source_id):
    print("Task Started")
    RefreshInventory(tenant_id, source_id).process()

@app.task
def launch_tower_job(slug, body):
    print("Launching job")
    obj = LaunchJob(slug, body).process()
    print(obj)
    print("finished")
