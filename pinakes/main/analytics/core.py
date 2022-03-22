import inspect
import io
import json
import logging
import os
import os.path
import pathlib
import shutil
import tarfile
import tempfile

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.timezone import now, timedelta
from django.db import connection
import requests

from pinakes.main.common.utils import (
    datetime_hook,
    advisory_lock,
)


__all__ = ["register", "gather", "ship"]

# TODO: add analytics logger
logger = logging.getLogger("analytics")

MAX_TABLE_SIZE = 200 * 1048576


class FileSplitter(io.StringIO):
    def __init__(self, filespec=None, *args, **kwargs):
        self.filespec = filespec
        self.files = []
        self.currentfile = None
        self.header = None
        self.counter = 0
        self.cycle_file()

    def cycle_file(self):
        if self.currentfile:
            self.currentfile.close()
        self.counter = 0
        fname = "{}_split{}".format(self.filespec, len(self.files))
        self.currentfile = open(fname, "w", encoding="utf-8")
        self.files.append(fname)
        if self.header:
            self.currentfile.write("{}\n".format(self.header))

    def file_list(self):
        self.currentfile.close()
        # Check for an empty dump
        if len(self.header) + 1 == self.counter:
            os.remove(self.files[-1])
            self.files = self.files[:-1]
        # If we only have one file, remove the suffix
        if len(self.files) == 1:
            filename = self.files.pop()
            new_filename = filename.replace("_split0", "")
            os.rename(filename, new_filename)
            self.files.append(new_filename)
        return self.files

    def write(self, s):
        if not self.header:
            self.header = s[: s.index("\n")]
        self.counter += self.currentfile.write(s)
        if self.counter >= MAX_TABLE_SIZE:
            self.cycle_file()


def copy_table(table, query, path):
    file_path = os.path.join(path, table + "_table.csv")
    file = FileSplitter(filespec=file_path)
    with connection.cursor() as cursor:
        cursor.copy_expert(query, file)
    return file.file_list()


def all_collectors():
    from pinakes.main.analytics import collectors

    return {
        func.__pinakes_analytics_key__: {
            "name": func.__pinakes_analytics_key__,
            "version": func.__pinakes_analytics_version__,
            "description": func.__pinakes_analytics_description__ or "",
        }
        for name, func in inspect.getmembers(collectors)
        if inspect.isfunction(func)
        and hasattr(func, "__pinakes_analytics_key__")
    }


def trivial_slicing(key, since, until, last_gather):
    if since is not None:
        return [(since, until)]

    horizon = until - timedelta(weeks=4)
    last_entries = settings.AUTOMATION_ANALYTICS_LAST_ENTRIES
    last_entries = json.loads(
        (last_entries.value if last_entries is not None else "") or "{}",
        object_hook=datetime_hook,
    )
    last_entry = max(last_entries.get(key) or last_gather, horizon)
    return [(last_entry, until)]


def four_hour_slicing(key, since, until, last_gather):
    if since is not None:
        last_entry = since
    else:
        horizon = until - timedelta(weeks=4)
        last_entries = None
        last_entries = json.loads(
            (last_entries.value if last_entries is not None else "") or "{}",
            object_hook=datetime_hook,
        )
        try:
            last_entry = max(last_entries.get(key) or last_gather, horizon)
        except TypeError:  # last_entries has a stale non-datetime entry for this collector
            last_entry = max(last_gather, horizon)

    start, end = last_entry, None
    while start < until:
        end = min(start + timedelta(hours=4), until)
        yield (start, end)
        start = end


def register(key, version, description=None, format="json", expensive=None):
    """
    A decorator used to register a function as a metric collector.

    Decorated functions should do the following based on format:
    - json: return JSON-serializable objects.
    - csv: write CSV data to a filename named 'key'

    @register('projects_by_scm_type', 1)
    def projects_by_scm_type():
        return {'git': 5, 'svn': 1}
    """

    def decorate(f):
        f.__pinakes_analytics_key__ = key
        f.__pinakes_analytics_version__ = version
        f.__pinakes_analytics_description__ = description
        f.__pinakes_analytics_type__ = format
        f.__pinakes_expensive__ = expensive
        return f

    return decorate


def package(target, data, timestamp):
    try:
        # tarname_base = f'{settings.SYSTEM_UUID}-{timestamp.strftime("%Y-%m-%d-%H%M%S%z")}'
        tarname_base = f'huis-{timestamp.strftime("%Y-%m-%d-%H%M%S%z")}'
        path = pathlib.Path(target)
        index = len(list(path.glob(f"{tarname_base}-*.*")))
        tarname = f"{tarname_base}-{index}.tar.gz"

        manifest = {}
        with tarfile.open(target.joinpath(tarname), "w:gz") as f:
            for name, (item, version) in data.items():
                try:
                    if isinstance(item, str):
                        f.add(item, arcname=f"./{name}")
                    else:
                        buf = json.dumps(item, cls=DjangoJSONEncoder).encode(
                            "utf-8"
                        )
                        info = tarfile.TarInfo(f"./{name}")
                        info.size = len(buf)
                        info.mtime = timestamp.timestamp()
                        f.addfile(info, fileobj=io.BytesIO(buf))
                    manifest[name] = version
                except Exception:
                    logger.exception(f"Could not generate metric {name}")
                    return None

            try:
                buf = json.dumps(manifest).encode("utf-8")
                info = tarfile.TarInfo("./manifest.json")
                info.size = len(buf)
                info.mtime = timestamp.timestamp()
                f.addfile(info, fileobj=io.BytesIO(buf))
            except Exception:
                logger.exception("Could not generate manifest.json")
                return None

        return f.name
    except Exception:
        logger.exception("Failed to write analytics archive file")
        return None


def calculate_collection_interval(since, until):
    _now = now()

    # Make sure that the endpoints are not in the future.
    if until is not None and until > _now:
        until = _now
        logger.warning(
            f"End of the collection interval is in the future, setting to {_now}."
        )
    if since is not None and since > _now:
        since = _now
        logger.warning(
            f"Start of the collection interval is in the future, setting to {_now}."
        )

    # The value of `until` needs to be concrete, so resolve it.  If it wasn't passed in,
    # set it to `now`, but only if that isn't more than 4 weeks ahead of a passed-in
    # `since` parameter.
    if since is not None:
        if until is not None:
            if until > since + timedelta(weeks=4):
                until = since + timedelta(weeks=4)
                logger.warning(
                    f"End of the collection interval is greater than 4 weeks from start, setting end to {until}."
                )
        else:  # until is None
            until = min(since + timedelta(weeks=4), _now)
    elif until is None:
        until = _now

    if since and since >= until:
        logger.warning(
            "Start of the collection interval is later than the end, ignoring request."
        )
        raise ValueError

    # The ultimate beginning of the interval needs to be compared to 4 weeks prior to
    # `until`, but we want to keep `since` empty if it wasn't passed in because we use that
    # case to know whether to use the bookkeeping settings variables to decide the start of
    # the interval.
    horizon = until - timedelta(weeks=4)
    if since is not None and since < horizon:
        since = horizon
        logger.warning(
            f"Start of the collection interval is more than 4 weeks prior to {until}, setting to {horizon}."
        )

    last_gather = settings.AUTOMATION_ANALYTICS_LAST_GATHER or horizon
    last_gather = horizon
    if last_gather < horizon:
        last_gather = horizon
        logger.warning(
            f"Last analytics run was more than 4 weeks prior to {until}, using {horizon} instead."
        )

    return since, until, last_gather


def gather(
    dest=None,
    module=None,
    subset=None,
    since=None,
    until=None,
    collection_type="scheduled",
):
    """
    Gather all defined metrics and write them as JSON files in a .tgz

    :param dest:   the (optional) absolute path to write a compressed tarball
    :param module: the module to search for registered analytic collector
                   functions; defaults to pinakes.main.analytics.collectors
    """
    log_level = (
        logging.ERROR if collection_type != "scheduled" else logging.DEBUG
    )

    with advisory_lock("gather_analytics_lock", wait=False) as acquired:
        if not acquired:
            logger.log(
                log_level, "Not gathering analytics, another task holds lock"
            )
            return None

        from pinakes.main.analytics import collectors

        # from pinakes.main.signals import disable_activity_stream

        logger.debug(
            "Last analytics run was: {}".format(
                settings.AUTOMATION_ANALYTICS_LAST_GATHER
            )
        )

        try:
            since, until, last_gather = calculate_collection_interval(
                since, until
            )
        except ValueError:
            return None

        # last_entries = settings.AUTOMATION_ANALYTICS_LAST_ENTRIES
        last_entries = None
        last_entries = json.loads(
            (last_entries.value if last_entries is not None else "") or "{}",
            object_hook=datetime_hook,
        )

        collector_module = module if module else collectors
        collector_list = [
            func
            for name, func in inspect.getmembers(collector_module)
            if inspect.isfunction(func)
            and hasattr(func, "__pinakes_analytics_key__")
            and (not subset or name in subset)
        ]
        if not any(
            c.__pinakes_analytics_key__ == "config" for c in collector_list
        ):
            # In order to ship to analytics, we must include the output of the built-in 'config' collector.
            collector_list.append(collectors.config)

        json_collectors = [
            func
            for func in collector_list
            if func.__pinakes_analytics_type__ == "json"
        ]
        csv_collectors = [
            func
            for func in collector_list
            if func.__pinakes_analytics_type__ == "csv"
        ]

        dest = pathlib.Path(
            dest or tempfile.mkdtemp(prefix="pinakes_analytics")
        )
        gather_dir = dest.joinpath("stage")
        gather_dir.mkdir(mode=0o700)
        tarfiles = []
        succeeded = True

        # These json collectors are pretty compact, so collect all of them before shipping to analytics.
        data = {}
        for func in json_collectors:
            key = func.__pinakes_analytics_key__
            filename = f"{key}.json"
            try:
                last_entry = max(
                    last_entries.get(key) or last_gather,
                    until - timedelta(weeks=4),
                )
                results = (
                    func(
                        since or last_entry,
                        collection_type=collection_type,
                        until=until,
                    ),
                    func.__pinakes_analytics_version__,
                )
                if bool(results[0]):  # only dump non-empty data
                    json.dumps(
                        results, cls=DjangoJSONEncoder
                    )  # throwaway check to see if the data is json-serializable
                    data[filename] = results
            except Exception:
                logger.exception(
                    "Could not generate metric {}".format(filename)
                )
        if data:
            if data.get("config.json") is None:
                logger.error("'config' collector data is missing.")
                return None

            tgzfile = package(dest.parent, data, until)
            if tgzfile is not None:
                tarfiles.append(tgzfile)
                if collection_type != "dry-run":
                    if ship(tgzfile):
                        # with disable_activity_stream():
                        #     for filename in data:
                        #         key = filename.replace('.json', '')
                        #         last_entries[key] = max(last_entries[key], until) if last_entries.get(key) else until
                        #     settings.AUTOMATION_ANALYTICS_LAST_ENTRIES = json.dumps(last_entries, cls=DjangoJSONEncoder)
                        for filename in data:
                            key = filename.replace(".json", "")
                            last_entries[key] = (
                                max(last_entries[key], until)
                                if last_entries.get(key)
                                else until
                            )
                        settings.AUTOMATION_ANALYTICS_LAST_ENTRIES = (
                            json.dumps(last_entries, cls=DjangoJSONEncoder)
                        )
                    else:
                        succeeded = False

        for func in csv_collectors:
            key = func.__pinakes_analytics_key__
            filename = f"{key}.csv"
            try:
                # These slicer functions may return a generator. The `since` parameter is
                # allowed to be None, and will fall back to LAST_ENTRIES[key] or to
                # LAST_GATHER (truncated appropriately to match the 4-week limit).
                if func.__pinakes_expensive__:
                    slices = func.__pinakes_expensive__(
                        key, since, until, last_gather
                    )
                else:
                    slices = trivial_slicing(key, since, until, last_gather)

                for start, end in slices:
                    files = func(start, full_path=gather_dir, until=end)

                    if not files:
                        if collection_type != "dry-run":
                            # with disable_activity_stream():
                            #     entry = last_entries.get(key)
                            #     last_entries[key] = max(entry, end) if entry and type(entry) == type(end) else end
                            #     settings.AUTOMATION_ANALYTICS_LAST_ENTRIES = json.dumps(last_entries, cls=DjangoJSONEncoder)
                            entry = last_entries.get(key)
                            last_entries[key] = (
                                max(entry, end)
                                if entry and type(entry) == type(end)
                                else end
                            )
                            settings.AUTOMATION_ANALYTICS_LAST_ENTRIES = (
                                json.dumps(last_entries, cls=DjangoJSONEncoder)
                            )
                        continue

                    slice_succeeded = True
                    for fpath in files:
                        payload = {
                            filename: (
                                fpath,
                                func.__pinakes_analytics_version__,
                            )
                        }

                        payload["config.json"] = data.get("config.json")
                        if payload["config.json"] is None:
                            logger.error(
                                "'config' collector data is missing, and is required to ship."
                            )
                            return None

                        tgzfile = package(dest.parent, payload, until)
                        if tgzfile is not None:
                            tarfiles.append(tgzfile)
                            if collection_type != "dry-run":
                                if not ship(tgzfile):
                                    slice_succeeded, succeeded = False, False
                                    break

                    if slice_succeeded and collection_type != "dry-run":
                        # with disable_activity_stream():
                        #     entry = last_entries.get(key)
                        #     last_entries[key] = max(entry, end) if entry and type(entry) == type(end) else end
                        #     settings.AUTOMATION_ANALYTICS_LAST_ENTRIES = json.dumps(last_entries, cls=DjangoJSONEncoder)
                        entry = last_entries.get(key)
                        last_entries[key] = (
                            max(entry, end)
                            if entry and type(entry) == type(end)
                            else end
                        )
                        settings.AUTOMATION_ANALYTICS_LAST_ENTRIES = (
                            json.dumps(last_entries, cls=DjangoJSONEncoder)
                        )
            except Exception:
                succeeded = False
                logger.exception(
                    "Could not generate metric {}".format(filename)
                )

        if collection_type != "dry-run":
            if succeeded:
                for fpath in tarfiles:
                    if os.path.exists(fpath):
                        os.remove(fpath)
            # with disable_activity_stream():
            #     if not settings.AUTOMATION_ANALYTICS_LAST_GATHER or until > settings.AUTOMATION_ANALYTICS_LAST_GATHER:
            #         # `AUTOMATION_ANALYTICS_LAST_GATHER` is set whether collection succeeds or fails;
            #         # if collection fails because of a persistent, underlying issue and we do not set last_gather,
            #         # we risk the collectors hitting an increasingly greater workload while the underlying issue
            #         # remains unresolved. Put simply, if collection fails, we just move on.

            #         # All that said, `AUTOMATION_ANALYTICS_LAST_GATHER` plays a much smaller role in determining
            #         # what is actually collected than it used to; collectors now mostly rely on their respective entry
            #         # under `last_entries` to determine what should be collected.
            #         settings.AUTOMATION_ANALYTICS_LAST_GATHER = until
            if (
                not settings.AUTOMATION_ANALYTICS_LAST_GATHER
                or until > settings.AUTOMATION_ANALYTICS_LAST_GATHER
            ):
                settings.AUTOMATION_ANALYTICS_LAST_GATHER = until

        shutil.rmtree(
            dest, ignore_errors=True
        )  # clean up individual artifact files
        if not tarfiles:
            # No data was collected
            logger.warning(
                "No data from {} to {}".format(since or last_gather, until)
            )
            return None

        return tarfiles


def ship(path):
    """
    Ship gathered metrics to the Insights API
    """
    if not path:
        logger.error("Insights for Ansible Automation Platform TAR not found")
        return False
    if not os.path.exists(path):
        logger.error(
            "Insights for Ansible Automation Platform TAR {} not found".format(
                path
            )
        )
        return False
    if "Error:" in str(path):
        return False

    logger.debug("shipping analytics file: {}".format(path))
    url = getattr(settings, "AUTOMATION_ANALYTICS_URL", None)
    # if not url:
    #     logger.error('AUTOMATION_ANALYTICS_URL is not set')
    #     return False

    rh_user = getattr(settings, "REDHAT_USERNAME", None)
    rh_password = getattr(settings, "REDHAT_PASSWORD", None)

    # if not rh_user:
    #     logger.error('REDHAT_USERNAME is not set')
    #     return False

    # if not rh_password:
    #     logger.error('REDHAT_PASSWORD is not set')
    #     return False

    # with open(path, 'rb') as f:
    #     files = {'file': (os.path.basename(path), f, settings.INSIGHTS_AGENT_MIME)}
    #     s = requests.Session()
    #     # s.headers = get_pinakes_http_client_headers()
    #     s.headers.pop('Content-Type')
    #     # with set_environ(**settings.AWX_TASK_ENV):
    #     response = s.post(
    #         url, files=files, verify="/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem", auth=(rh_user, rh_password), headers=s.headers, timeout=(31, 31)
    #     )
    #     # Accept 2XX status_codes
    #     if response.status_code >= 300:
    #         logger.error('Upload failed with status {}, {}'.format(response.status_code, response.text))
    #         return False

    #     return True
    return True
