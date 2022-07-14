"""Module to test GET/POST to Tower"""
import pytest
import responses
import requests
from pinakes.main.inventory.task_utils.tower_api import (
    TowerAPI,
)


class TestTowerAPI:
    """TestTowerAPI fetches objects from tower"""

    @responses.activate
    def test_fetch_multiple_pages(self):
        """Test fetching multiple pages and yield one object at a time to
        the caller.
        """
        data1 = {
            "count": 3,
            "next": "/api/v2/job_templates/?page=2",
            "previous": None,
            "results": [
                {
                    "name": "abc",
                    "description": "desc1",
                    "related": {"inventory": 2},
                },
                {
                    "name": "xyz",
                    "description": "desc2",
                    "related": {"inventory": 3},
                },
            ],
        }
        data2 = {
            "count": 3,
            "previous": "/api/v2/job_templates/?page=1",
            "next": None,
            "results": [
                {
                    "name": "mno",
                    "description": "desc3",
                    "related": {"inventory": 5},
                },
            ],
        }
        tower_api = TowerAPI(
            "https://www.example.com", "gobbledegook", "false"
        )
        responses.add(
            responses.GET,
            "https://www.example.com/api/v2/job_templates",
            json=data1,
            status=200,
        )
        responses.add(
            responses.GET,
            "https://www.example.com/api/v2/job_templates/?page=2",
            json=data2,
            status=200,
        )

        names = []
        for obj in tower_api.get(
            "/api/v2/job_templates",
            ["name", "description", "related.inventory"],
        ):
            names.append(obj["name"])

        assert (names) == ["abc", "xyz", "mno"]

    @responses.activate
    def test_single_object(self):
        """Fetch a single object from tower sans pagination data"""
        data = {
            "name": "abc",
            "description": "desc1",
            "related": {"inventory": 2},
            "summary": {"info": {"version": "2.0"}},
        }
        tower_api = TowerAPI(
            "https://www.example.com", "gobbledegook", "false"
        )
        responses.add(
            responses.GET,
            "https://www.example.com/api/v2/job_templates/1/",
            json=data,
            status=200,
        )
        names = []
        for obj in tower_api.get(
            "/api/v2/job_templates/1/",
            [
                "name",
                "description",
                "related.inventory",
                "summary.info.missing",
            ],
        ):
            names.append(obj["name"])
            assert obj["summary.info.missing"] is None

        assert (names) == ["abc"]

    @responses.activate
    def test_errors(self):
        """Test errors when we get HTTP Error Codes"""
        tower_api = TowerAPI(
            "https://www.example.com", "gobbledegook", "false"
        )
        responses.add(
            responses.GET,
            "https://www.example.com/api/v2/job_templates/1/",
            json={"error": "not found"},
            status=404,
        )
        with pytest.raises(RuntimeError, match=r"not found"):
            for _ in tower_api.get(
                "/api/v2/job_templates/1/",
                ["name", "description", "related.inventory"],
            ):
                pass

    @responses.activate
    def test_exception(self):
        """Test exceptions raised by the requests module"""
        tower_api = TowerAPI(
            "https://www.example.com", "gobbledegook", "false"
        )
        responses.add(
            responses.GET,
            "https://www.example.com/api/v2/job_templates/1/",
            body=requests.exceptions.RequestException("Kaboom"),
        )
        with pytest.raises(
            requests.exceptions.RequestException, match=r"Kaboom"
        ):
            for _ in tower_api.get(
                "/api/v2/job_templates/1/",
                ["name", "description", "related.inventory"],
            ):
                pass

    @responses.activate
    def test_post(self):
        """Test POST with JSON body"""
        job_url = "/api/v2/jobs/123/"
        tower_api = TowerAPI(
            "https://www.example.com", "gobbledegook", "false"
        )
        data = {
            "url": job_url,
            "status": "running",
            "artifacts": {"inventory": 2},
        }
        responses.add(
            responses.POST,
            "https://www.example.com/api/v2/job_templates/1/launch/",
            json=data,
            status=200,
        )
        obj = tower_api.post(
            "/api/v2/job_templates/1/launch/",
            {"name": "Fred"},
            ["url", "status"],
        )
        assert (obj["url"]) == job_url

    @responses.activate
    def test_post_exception(self):
        """Test POST exceptions raised by the requests module"""
        tower_api = TowerAPI(
            "https://www.example.com", "gobbledegook", "false"
        )
        responses.add(
            responses.POST,
            "https://www.example.com/api/v2/job_templates/1/launch/",
            body=requests.exceptions.RequestException("Kaboom"),
        )
        with pytest.raises(
            requests.exceptions.RequestException, match=r"Kaboom"
        ):
            tower_api.post("/api/v2/job_templates/1/launch/", {"a": 1}, [])

    @responses.activate
    def test_post_errors(self):
        """Test POST errors when we get HTTP Error Codes"""
        tower_api = TowerAPI(
            "https://www.example.com", "gobbledegook", "false"
        )
        responses.add(
            responses.POST,
            "https://www.example.com/api/v2/job_templates/1/launch/",
            json={"error": "not found"},
            status=404,
        )
        with pytest.raises(RuntimeError, match=r"not found"):
            tower_api.post("/api/v2/job_templates/1/launch/", {"a": 1}, [])

    testdata = [("y", True), ("n", False), ("true", True), ("false", False)]

    @pytest.mark.parametrize("value,expected", testdata)
    def test_verify_ssl_boolean(self, value, expected):
        """Check if verify_ssl is proper boolean"""
        tower_api = TowerAPI("https://www.example.com", "gobbledegook", value)
        assert (tower_api.verify_ssl) == expected

    def test_verify_ssl_ca_file(self, tmpdir):
        """Check if verify_ssl is ca_file"""
        ca_file = tmpdir.join("ca.crt")
        ca_file.write("dummy")
        tower_api = TowerAPI(
            "https://www.example.com",
            "gobbledegook",
            str(ca_file),
        )
        assert (tower_api.verify_ssl) == str(ca_file)
