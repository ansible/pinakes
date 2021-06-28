""" Tower API module interacts using the REST API to
    1. Get a single object
    2. Get multiple objects with pagination info
    3. POST a Job Template/Workflow
"""
from distutils.util import strtobool
import base64
from django.conf import settings
import requests

requests.packages.urllib3.disable_warnings()

class TowerAPI:
    """TowerAPI class supports GET/POST to tower given a slug"""

    VALID_POST_CODES = [200, 201, 202]
    VALID_GET_CODES = [200]

    def __init__(self, url=None, token=None, verify_ssl=None):
        if url is None:
            url = settings.TOWER_URL
        self.url = url.rstrip("/")

        if token is None:
            token = settings.TOWER_TOKEN

        if verify_ssl is None:
            verify_ssl = settings.TOWER_VERIFY_SSL

        self.verify_ssl = strtobool(verify_ssl)

        self.headers = {"Authorization": f"Bearer {token}"}

        # user_pass = "admin:PeaQE!23"
        # encoded_u = base64.b64encode(user_pass.encode()).decode()
        # self.headers = {"Authorization": f"Basic {encoded_u}"}

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
                            yield self.__filtered(payload, attrs)
                    else:
                        yield self.__filtered(data, attrs)
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
                return self.__filtered(data, attrs)

            raise RuntimeError(
                "POST failed %s status %s body %s"
                % (slug, response.status_code, response.text)
            )
        except requests.exceptions.RequestException as exc:
            raise exc

    def __filtered(self, payload, attrs):
        """Build an object by filtering out unwanted variables"""
        obj = {}
        for attr in attrs:
            if self.attr_delimiter in attr:
                data = payload
                for key in attr.split(self.attr_delimiter):
                    data = data[key]
                obj[attr] = data
            else:
                obj[attr] = payload[attr]
        return obj
