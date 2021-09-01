"""Tag operations for Approval"""

from enum import Enum


class OperateTag:
    """Tag operations for Approval"""

    Operation = Enum("Operation", ["Add", "Remove", "Find"])

    def __init__(self, instance):
        self.instance = instance

    def process(self, operation, tag):
        if operation == OperateTag.Operation.Add:
            self.instance.tags.add(tag)
        elif operation == OperateTag.Operation.Remove:
            self.instance.tags.remove(tag)

        return self
