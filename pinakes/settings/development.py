"""Development Settings
    When running pytest SQLite is used as Database
    Supports local settings in pinakes/settings/local*.py
"""
# flake8: noqa
import sys
import traceback

# Django Split Settings
from split_settings.tools import optional, include

# Load Default Settings
from .defaults import *

# If any local_*.py files are present in pinakes/settings/,
# use them to override default settings for development.
# If not present, we can still run using only the defaults.
try:
    include(optional("local_*.py"), scope=locals())
except ImportError:
    traceback.print_exc()
    sys.exit(1)

# Use SQLite for unit tests instead of PostgreSQL
if "pytest" in sys.modules:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "catalog_test.db",
        },
    }

ALLOWED_HOSTS = ["*"]
CONTROLLER_VERIFY_SSL = "False"

# Allow CORS for UI development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
