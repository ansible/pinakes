"""Response to events when an approval request changes state"""
from main.catalog.models import Order


class ReceiveApprovalEvents:
    """ReceiveApprovalEvent service class"""

    def __init__(self, event, **kwargs):
        pass

    def process(self):
        return self
