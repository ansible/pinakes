"""Test copy name service"""

from ansible_catalog.main.catalog.services.copy_name import CopyName


def test_copy_name_with_empty_names():
    names = []
    copied_name = CopyName.create_copy_name("My test", names)

    assert copied_name == "Copy of My test"


def test_copy_name_with_copied_names():
    names = [
        "Copy of My test",
    ]
    copied_name = CopyName.create_copy_name("My test", names)

    assert copied_name == "Copy (1) of My test"


def test_copy_name_with_multiple_copied_names():
    names = [
        "My test",
        "Copy of My test",
        "Copy (1) of My test",
        "Copy (100) of My test",
    ]
    copied_name = CopyName.create_copy_name("My test", names)

    assert copied_name == "Copy (101) of My test"


def test_copy_name_with_truncate_copied_names():
    names = []
    copied_name = CopyName.create_copy_name("My test", names, 12)

    assert copied_name == "Copy of My t"
