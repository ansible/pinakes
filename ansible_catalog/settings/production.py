""" Production Settings
    defined in /etc/ansible_catalog/settings.py or in
               /etc/ansible_catalog/conf.d/settings.py
"""
import sys
import os
import traceback
import errno

# Django Split Settings
from split_settings.tools import optional, include

# Clear database settings to force production environment to define them.
DATABASES = {}

# Clear the secret key to force production environment to define it.
SECRET_KEY = None

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

DEBUG = False
TEMPLATE_DEBUG = DEBUG
SQL_DEBUG = DEBUG

# Load settings from any .py files in the global conf.d directory specified in
# the environment, defaulting to /etc/ansible_catalog/conf.d/.
settings_dir = os.environ.get(
    "CATALOG_SETTINGS_DIR", "/etc/ansible_catalog/conf.d/"
)
settings_files = os.path.join(settings_dir, "*.py")

# Load remaining settings from the global settings file specified in the
# environment, defaulting to /etc/ansible_catalog/settings.py.
settings_file = os.environ.get(
    "CATALOG_SETTINGS_FILE", "/etc/ansible_catalog/settings.py"
)

# Attempt to load settings from /etc/ansible_catalog/settings.py first, followed by
# /etc/ansible_catalog/conf.d/*.py.
try:
    include(settings_file, optional(settings_files), scope=locals())
except ImportError:
    traceback.print_exc()
    sys.exit(1)
except IOError:
    from django.core.exceptions import ImproperlyConfigured

    included_file = locals().get("__included_file__", "")
    if not included_file or included_file == settings_file:
        # The import doesn't always give permission denied, so try to open the
        # settings file directly.
        try:
            e = None
            open(settings_file)
        except IOError:
            pass
        if e and e.errno == errno.EACCES:
            SECRET_KEY = "permission-denied"
            LOGGING = {}
        else:
            msg = "No CATALOG configuration found at %s." % settings_file
            msg += (
                "\nDefine the CATALOG_SETTINGS_FILE environment variable to "
            )
            msg += "specify an alternate path."
            raise ImproperlyConfigured(msg)
    else:
        raise
