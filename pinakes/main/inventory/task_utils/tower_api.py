"""Tower API module interacts using the REST API to
    1. Get a single object
    2. Get multiple objects with pagination info
    3. POST a Job Template/Workflow
"""
from pathlib import Path
from distutils.util import strtobool
from django.conf import settings
import requests

requests.packages.urllib3.disable_warnings()


class TowerAPI:
    """TowerAPI class supports GET/POST to tower given a slug"""

    VALID_POST_CODES = [200, 201, 202]
    VALID_GET_CODES = [200]

    def __init__(self, url=None, token=None, verify_ssl=None):
        if url is None:
            url = settings.CONTROLLER_URL
        self.url = url.rstrip("/")

        if token is None:
            token = settings.CONTROLLER_TOKEN

        if verify_ssl is None:
            verify_ssl = settings.CONTROLLER_VERIFY_SSL

        if Path(verify_ssl).is_file():
            self.verify_ssl = verify_ssl
        else:
            self.verify_ssl = bool(strtobool(verify_ssl))

        self.headers = {"Authorization": f"Bearer {token}"}

        self.attr_delimiter = "."

    def get(self, obj_url, attrs):
        """This generator function fetches objects from multiple pages and
        yields one object at a time to the caller
        """
        next_url = obj_url
        try:
            while next_url:
                response = requests.get(
                    f"{self.url}{next_url}",
                    headers=self.headers,
                    verify=self.verify_ssl,
                )
                if response.status_code in self.VALID_GET_CODES:
                    data = response.json()
                    next_url = data.get("next", None)
                    if "results" in data:
                        for payload in data["results"]:
                            yield self._filtered(payload, attrs)
                    else:
                        yield self._filtered(data, attrs)
                else:
                    raise RuntimeError(
                        "GET failed %s status %s body %s"
                        % (next_url, response.status_code, response.text)
                    )
        except requests.exceptions.RequestException as exc:
            raise exc

    def post(self, slug, payload, attrs):
        """Post to a URL and get the response back
        the payload is a  python dictionary and will be
        sent up as json
        """
        try:
            response = requests.post(
                f"{self.url}{slug}",
                headers=self.headers,
                verify=self.verify_ssl,
                json=payload,
            )
            if response.status_code in self.VALID_POST_CODES:
                data = response.json()
                return self._filtered(data, attrs)

            raise RuntimeError(
                "POST failed %s status %s body %s"
                % (slug, response.status_code, response.text)
            )
        except requests.exceptions.RequestException as exc:
            raise exc

    def _filtered(self, payload, attrs):
        """Build an object by filtering out unwanted variables"""
        obj = {}
        for attr in attrs:
            if self.attr_delimiter in attr:
                data = payload
                for key in attr.split(self.attr_delimiter):
                    if key in data:
                        data = data[key]
                    else:
                        data = None
                        break
                obj[attr] = data
            else:
                obj[attr] = payload.get(attr, None)
        return obj
