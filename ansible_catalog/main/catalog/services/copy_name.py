"""Create new copied name"""

import re


class CopyName:
    """Create new copy name"""

    name_pattern = (
        "^Copy \((\d+)\) of"  # pattern of "Copy (2) of original_name"
    )

    @staticmethod
    def create_copy_name(original_name, existing_names, max_length=64):
        copied_name = CopyName.copy(original_name, existing_names)

        return copied_name[:max_length] if max_length else copied_name

    @staticmethod
    def copy(original_name, names):
        copied_name = "Copy of %s" % original_name

        if copied_name in names:
            i = CopyName.get_index(names)
            copied_name = "Copy (%d) of %s" % (i + 1, original_name)

        return copied_name

    @staticmethod
    def get_index(names):
        indexes = [
            int(re.match(CopyName.name_pattern, name).groups()[0])
            for name in names
            if re.match(CopyName.name_pattern, name) is not None
        ]

        return max(indexes) if len(indexes) > 0 else 0
