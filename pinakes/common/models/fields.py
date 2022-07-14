import functools
import json

from cryptography.fernet import Fernet, MultiFernet
from django.conf import settings
from django.core import checks
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import gettext_lazy as _


class EncryptedJsonField(models.Field):
    empty_strings_allowed = False
    description = _("An encrypted JSON object")
    _restricted_parameters = [
        "db_index",
        "unique",
        "unique_for_date",
        "unique_for_month",
        "unique_for_year",
        "choices",
    ]

    def get_internal_type(self):
        return "TextField"

    def check(self, **kwargs):
        return [
            *super().check(**kwargs),
            *self._check_restricted_parameters(),
        ]

    def _check_restricted_parameters(self):
        errors = []
        for param in self._restricted_parameters:
            if getattr(self, param):
                error = checks.Error(
                    f"{self.__class__.__name__} does not support '{param}'.",
                    obj=self,
                    id="pinakes.E001",
                )
                errors.append(error)
        return errors

    def from_db_value(self, value, _expression, _connection):
        if value is None:
            return None
        value = fernet().decrypt(value.encode("ascii")).decode("utf-8")
        return json.loads(value)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None:
            return None
        value = json.dumps(value)
        return fernet().encrypt(value.encode("utf-8")).decode("ascii")


@functools.lru_cache(maxsize=None)
def fernet() -> MultiFernet:
    try:
        keys = settings.DB_ENCRYPTION_KEYS
    except AttributeError:
        raise ImproperlyConfigured("DB_ENCRYPTION_KEYS must be set")
    if not keys:
        raise ImproperlyConfigured("DB_ENCRYPTION_KEYS cannot be empty")
    return MultiFernet(map(Fernet, keys))
