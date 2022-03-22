from contextlib import contextmanager

# from django_pglocks import advisory_lock as django_pglocks_advisory_lock
from django.db import connection

from django.utils.dateparse import parse_datetime


@contextmanager
def advisory_lock(*args, **kwargs):
    if connection.vendor == "postgresql":
        # with django_pglocks_advisory_lock(*args, **kwargs) as internal_lock:
        #     yield internal_lock
        yield True
    else:
        yield True


def datetime_hook(d):
    new_d = {}
    for key, value in d.items():
        try:
            new_d[key] = parse_datetime(value)
        except TypeError:
            new_d[key] = value
    return new_d
