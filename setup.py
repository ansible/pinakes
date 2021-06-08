#!/usr/bin/env python
""" Setup Module """


import os
from setuptools import setup


def get_version():
    """Read version from VERSION file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    version_file = os.path.join(current_dir, "VERSION")
    with open(version_file, "r") as file:
        return file.read().strip()


setup(
    name="ansible-catalog",
    version=get_version(),
    author="Ansible, Inc.",
    author_email="info@ansible.com",
    description="Ansible Services Catalog adds governance to Job Templates and Workflows",
    license="Apache License 2.0",
    keywords="ansible, catalog",
    url="http://github.com/ansible/ansiblc-catalog",
    packages=["ansible-catalog"],
)
