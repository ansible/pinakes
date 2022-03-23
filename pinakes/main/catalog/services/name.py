"""Create new copied name"""

import re


NAME_PATTERN = (  # pattern of "Copy (2) of original_name"
    "^Copy \\((\\d+)\\) of"
)
MAX_LENGTH = 64


def create_copy_name(original_name, existing_names, max_length=MAX_LENGTH):
    copied_name = copy(original_name, existing_names)

    return copied_name[:max_length] if max_length else copied_name


def copy(original_name, names):
    copied_name = f"Copy of {original_name}"

    if copied_name in names:
        i = get_index(names)
        copied_name = f"Copy ({i+1}) of {original_name}"

    return copied_name


def get_index(names):
    indexes = [
        int(re.match(NAME_PATTERN, name).groups()[0])
        for name in names
        if re.match(NAME_PATTERN, name) is not None
    ]

    return max(indexes) if len(indexes) > 0 else 0
