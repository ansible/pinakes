from __future__ import annotations

from typing import Any, Mapping, Optional, Union

import requests

from . import exceptions


class ApiClient:
    def __init__(
        self, token: Optional[str] = None, verify_ssl: Union[bool, str] = True
    ):
        self.token = token

        self._session = requests.Session()
        self._session.verify = verify_ssl

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Any = None,
        headers: Mapping[str, str] = None,
        data: Any = None,
        json: Any = None,
    ):
        headers_out = {}
        if self.token:
            headers_out["Authorization"] = f"Bearer {self.token}"
        if headers:
            headers_out.update(headers)
        response = self._session.request(
            method,
            url,
            params=params,
            data=data,
            headers=headers_out,
            json=json,
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            self.exception_handler(e)

        return response

    def request_json(
        self,
        method: str,
        url: str,
        *,
        params: Any = None,
        headers: Mapping[str, str] = None,
        data: Any = None,
        json: Any = None,
    ):
        headers_out = {"Accept": "application/json"}
        if headers:
            headers_out.update(headers)
        return self.request(
            method,
            url,
            params=params,
            headers=headers_out,
            data=data,
            json=json,
        ).json()

    def exception_handler(self, e: requests.HTTPError):
        error = None
        error_description = None
        try:
            data = e.response.json()
        except ValueError:
            pass
        else:
            if isinstance(data, dict):
                error = data.get("error")
                error_description = data.get("error_description")

        status_code = e.response.status_code
        exception_cls = exceptions.get_http_exception_class(status_code)
        raise exception_cls(error, error_description, status_code) from e
