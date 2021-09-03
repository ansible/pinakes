"""Tag operations for Approval"""

from enum import Enum


class OperateTag:
    """Tag operations for Approval"""

    Operation = Enum("Operation", ["ADD", "REMOVE"])

    def __init__(self, instance):
        self.instance = instance

    def process(self, operation, tag):
        if operation == self.Operation.ADD:
            self.instance.tags.add(tag)
        elif operation == self.Operation.REMOVE:
            self.instance.tags.remove(tag)

        return self
